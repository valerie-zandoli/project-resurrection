"""Numerical preview using the explicitly recorded proposed model conventions."""

import copy
import csv
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path

import jsonschema

from validators.handoff_hashes import check_files_current, file_sha256
from validators.parameters import validate_parameters

REPO = Path(__file__).resolve().parents[1]


@dataclass
class Lynx:
    id: str
    sex: str
    age_months: int
    patch_id: str
    alive: bool = True
    settled: bool = False


@dataclass(frozen=True)
class Parameters:
    breeding_min: int
    breeding_max: int
    breeding_probability: float
    birth_month: int
    litter_min: int
    litter_max: int
    female_probability: float
    dispersal_age: int
    survival_3: float
    survival_10: float
    survival_dispersal: float
    annual_mortality: float
    home_range: float
    food_threshold: float

    def survival(self, age):
        if age < 3:
            return self.survival_3 ** (1 / 3)
        if age < 10:
            return (self.survival_10 / self.survival_3) ** (1 / 7)
        if age < self.dispersal_age:
            return (self.survival_dispersal / self.survival_10) ** (1 / (self.dispersal_age - 10))
        return (1 - self.annual_mortality) ** (1 / 12)


def schema(name):
    return json.loads((REPO / 'schemas' / f'{name}.schema.json').read_text())


def research_path(root, name):
    path = (Path(root) / name).resolve()
    if Path(name).is_absolute() or not path.is_relative_to(Path(root).resolve()):
        raise ValueError('Research paths must stay inside the repository')
    return path


def load_parameters(config, root):
    paths = [research_path(root, config[k]) for k in ('parameters_csv', 'sources_csv')]
    errors = check_files_current(config, root) + validate_parameters(*paths)
    if errors:
        raise ValueError('\n'.join(errors))
    with paths[0].open(encoding='utf-8-sig', newline='') as handle:
        rows = {r['name']: r for r in csv.DictReader(handle)}

    def value(name, units, column='baseline'):
        if name not in rows or rows[name]['units'] != units:
            raise ValueError(f'{name}: missing parameter or unexpected units (expected {units})')
        return float(rows[name][column])

    def integer(number):
        if not number.is_integer():
            raise ValueError('Age, month, and litter bounds must be whole numbers')
        return int(number)

    overrides = config['parameter_overrides']
    minimum = integer(12 * value('breeding_age_min', 'years'))
    maximum = integer(12 * value('breeding_age_max', 'years'))
    ratio = value('sex_ratio_female_per_male_at_birth', 'females per male')
    if ratio < 0:
        raise ValueError('Female-to-male birth ratio must be nonnegative')
    p = Parameters(
        minimum, maximum,
        value('annual_breeding_probability', 'probability per female per year'),
        integer(value('birth_month', 'month of year (3 = March)')),
        integer(value('litter_size_at_birth', 'cubs per litter', 'low')),
        integer(value('litter_size_at_birth', 'cubs per litter', 'high')),
        ratio / (1 + ratio),
        integer(value('dispersal_age_months', 'months')),
        value('cub_cumulative_survival_3mo', 'proportion alive, cumulative from birth'),
        value('cub_cumulative_survival_10mo', 'proportion alive, cumulative from birth'),
        value('cub_cumulative_survival_to_dispersal', 'proportion alive, cumulative from birth'),
        overrides.get('annual_mortality_rate_all_causes', value('annual_mortality_rate_all_causes', 'probability of death per year')),
        overrides.get('female_home_range_km2', value('female_home_range_km2', 'square kilometres')),
        overrides.get('rabbit_density_spring_min_for_territorial_breeding', value('rabbit_density_spring_min_for_territorial_breeding', 'rabbits per hectare, spring')),
    )
    if not (0 < p.survival_dispersal <= p.survival_10 <= p.survival_3 <= 1):
        raise ValueError('Cumulative survival must be positive and nonincreasing')
    if not (10 < p.dispersal_age <= p.breeding_min <= p.breeding_max):
        raise ValueError('Require 10 < dispersal age <= breeding minimum <= maximum')
    if not (0 <= p.breeding_probability <= 1 and 0 <= p.annual_mortality <= 1
            and 1 <= p.birth_month <= 12 and 0 <= p.litter_min <= p.litter_max
            and ratio >= 0 and p.home_range > 0 and p.food_threshold >= 0):
        raise ValueError('Invalid biological parameter bounds')
    return p


def validate_config(config, p):
    pop = config['initial_population']
    if not (p.dispersal_age <= pop['age_months_min'] <= pop['age_months_max']):
        raise ValueError('Starting age bounds must be ordered and at/above dispersal age')
    patches = config['patches']
    if len({patch['id'] for patch in patches}) != 2:
        raise ValueError('Patch IDs must be distinct')
    if any(patch['habitat_quality'] != 1.0 for patch in patches):
        raise ValueError('The agreed area experiment requires habitat_quality=1.0')
    if pop['females'] % 2 or pop['males'] % 2:
        raise ValueError('Equal allocation to two patches requires even counts per sex')
    if any(pop['females'] // 2 > math.floor(patch['area_km2'] / p.home_range) for patch in patches):
        raise ValueError('Starting females exceed territory capacity; choose a feasible initialization')


def breeding_age(animal, p):
    return animal.alive and p.breeding_min <= animal.age_months <= p.breeding_max


def persisted(animals, p):
    male_patches = {a.patch_id for a in animals if a.sex == 'male' and breeding_age(a, p)}
    return any(a.sex == 'female' and a.settled and breeding_age(a, p)
               and a.patch_id in male_patches for a in animals)


def counts(animals, month, births=0, deaths=0, movements=0):
    living = [a for a in animals if a.alive]
    females = sum(a.sex == 'female' for a in living)
    return dict(month=month, population=len(living), females=females,
                males=len(living) - females, births=births, deaths=deaths, movements=movements)


def check_states(animals, capacities):
    if len({a.id for a in animals}) != len(animals):
        raise ValueError('Duplicate animal ID')
    for a in animals:
        if a.patch_id not in capacities or (a.settled and (not a.alive or a.sex != 'female')):
            raise ValueError('Invalid patch or territory holder')
    for patch, capacity in capacities.items():
        if sum(a.alive and a.settled and a.patch_id == patch for a in animals) > capacity:
            raise ValueError('Female territory capacity exceeded')


def advance(animals, config, p, rng, month, capacities):
    deaths = 0
    moved = set()
    for animal in animals:
        if not animal.alive:
            continue
        if rng.random() >= p.survival(animal.age_months):
            animal.alive = False
            animal.settled = False
            deaths += 1
        else:
            animal.age_months += 1

    patch_ids = list(capacities)
    occupied = {patch: sum(a.alive and a.settled and a.patch_id == patch for a in animals)
                for patch in patch_ids}
    candidates = [a for a in animals if a.alive and a.sex == 'female'
                  and not a.settled and a.age_months >= p.dispersal_age]
    rng.shuffle(candidates)
    for animal in candidates:
        other = next(patch for patch in patch_ids if patch != animal.patch_id)
        for patch in (animal.patch_id, other):
            if occupied[patch] < capacities[patch]:
                if patch != animal.patch_id:
                    moved.add(animal.id)
                animal.patch_id = patch
                animal.settled = True
                occupied[patch] += 1
                break
    for animal in animals:
        if (animal.alive and animal.sex == 'male' and animal.age_months >= p.breeding_min
                and rng.random() < config['male_patch_crossing_probability']):
            animal.patch_id = next(patch for patch in patch_ids if patch != animal.patch_id)
            moved.add(animal.id)

    births = []
    calendar_month = (config['start_month'] - 1 + month) % 12 + 1
    if calendar_month == p.birth_month and config['food_rabbits_per_ha'] >= p.food_threshold:
        male_patches = {a.patch_id for a in animals if a.sex == 'male' and breeding_age(a, p)}
        for mother in animals:
            if (mother.sex == 'female' and mother.settled and breeding_age(mother, p)
                    and mother.patch_id in male_patches and rng.random() < p.breeding_probability):
                for _ in range(rng.randint(p.litter_min, p.litter_max)):
                    births.append(Lynx(f'lynx-{len(animals) + len(births) + 1:06d}',
                                       'female' if rng.random() < p.female_probability else 'male',
                                       0, mother.patch_id))
    animals.extend(births)
    check_states(animals, capacities)
    return counts(animals, month, len(births), deaths, len(moved))


def run_model(config, p):
    """Pure seeded calculation; callers must validate the external input first."""
    validate_config(config, p)
    rng = random.Random(config['seed'])
    pop = config['initial_population']
    capacities = {patch['id']: math.floor(patch['area_km2'] / p.home_range)
                  for patch in config['patches']}
    animals = []
    for sex in ('female', 'male'):
        for i in range(pop[sex + 's']):
            patch = config['patches'][i % 2]['id']
            animals.append(Lynx(f'lynx-{len(animals) + 1:06d}', sex,
                                rng.randint(pop['age_months_min'], pop['age_months_max']),
                                patch, settled=sex == 'female'))
    check_states(animals, capacities)
    history = [counts(animals, 0)]
    for month in range(1, config['duration_months'] + 1):
        row = advance(animals, config, p, rng, month, capacities)
        if row['population'] != history[-1]['population'] + row['births'] - row['deaths']:
            raise ValueError('Population accounting failed')
        history.append(row)
    return dict(schema_version='3.0', run_id=config['run_id'], data_kind='simulation',
                seed=config['seed'], revision_round=0, config=copy.deepcopy(config),
                history=history, final_animals=[asdict(a) for a in animals],
                persisted=persisted(animals, p), assumptions=[
                    'Synthetic preview, not historical validation or a live multi-agent workflow.',
                    'Provisional: survival, aging, settlement, male movement, births, recording.',
                    'Provisional: uniform integer litter size across the table range.',
                    'Provisional: unsettled females try both patches monthly in seeded random order.',
                    'Mortality transfers older abstract evidence; dispersal at 18 months is assumed.',
                    'Food affects breeding only; density is constant; habitat_quality is 1.0.',
                ])


def simulate(config, root=REPO):
    config = copy.deepcopy(config)
    # JSON rejects NaN/infinity before schema numeric comparisons can accept them.
    json.dumps(config, allow_nan=False)
    jsonschema.validate(config, schema('input'))
    p = load_parameters(config, root)
    result = run_model(config, p)
    errors = check_files_current(config, root)
    if errors:
        raise ValueError('\n'.join(errors))
    jsonschema.validate(result, schema('results'))
    return result


def summary(result):
    history = result['history']
    extinction = next((row['month'] for row in history if row['population'] == 0), None)
    return dict(run_id=result['run_id'], persisted=result['persisted'],
                final_population=history[-1]['population'], extinction_month=extinction,
                births_final_12_months=sum(row['births'] for row in history[-12:]),
                historical_validation='not_assessed', model_conventions=result['config']['model_conventions'])


def preview_config(seed=42, months=12, food=4.6, area=50, root=REPO):
    config = json.loads((REPO / 'examples/handoffs/input.json').read_text())
    config.update(run_id=f'preview-{seed}', seed=seed, duration_months=months,
                  food_rabbits_per_ha=food)
    for patch in config['patches']:
        patch['area_km2'] = area
    for field in ('parameters', 'sources'):
        config[field + '_sha256'] = file_sha256(research_path(root, config[field + '_csv']))
    return config
