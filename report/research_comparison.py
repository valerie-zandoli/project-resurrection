"""Describe actual saved research inputs without turning model output into observations."""
import csv
import math

from simulation.model import load_parameters, research_path
from validators.evidence_gate import EVIDENCE_FILE


def research_comparison(config, results, snapshot):
    p = load_parameters(config, snapshot)
    def read(path, key):
        with path.open(encoding='utf-8-sig', newline='') as handle:
            return {row[key]: row for row in csv.DictReader(handle)}
    parameters = read(research_path(snapshot, config['parameters_csv']), 'name')
    sources = read(research_path(snapshot, config['sources_csv']), 'key')
    evidence_path = research_path(snapshot, EVIDENCE_FILE)
    evidence = read(evidence_path, 'name') if evidence_path.is_file() else {}
    used = [
        ('rabbit_density_spring_min_for_territorial_breeding', 'Food threshold for breeding', p.food_threshold, 'rabbits per hectare', ['birth_timing_and_food']),
        ('female_home_range_km2', 'Territory per female', p.home_range, 'square kilometres', ['territory_capacity']),
        ('breeding_age_min', 'Youngest breeding age', p.breeding_min / 12, 'years', []),
        ('breeding_age_max', 'Oldest breeding age', p.breeding_max / 12, 'years', []),
        ('annual_breeding_probability', 'Annual breeding chance', p.breeding_probability, 'probability per eligible female per year', []),
        ('litter_size_at_birth', 'Cubs per litter', [p.litter_min, p.litter_max], 'cubs; model samples whole numbers within these bounds', []),
        ('cub_cumulative_survival_3mo', 'Survival from birth to 3 months', p.survival_3, 'cumulative proportion', []),
        ('cub_cumulative_survival_10mo', 'Survival from birth to 10 months', p.survival_10, 'cumulative proportion', []),
        ('cub_cumulative_survival_to_dispersal', 'Survival from birth to dispersal', p.survival_dispersal, 'cumulative proportion', []),
        ('sex_ratio_female_per_male_at_birth', 'Female-to-male birth ratio', float(parameters['sex_ratio_female_per_male_at_birth']['baseline']), 'females per male', []),
        ('birth_month', 'Breeding season: birth month', p.birth_month, 'month number; 3 means March', ['birth_timing_and_food']),
        ('dispersal_age_months', 'Dispersal age', p.dispersal_age, 'months', []),
        ('annual_mortality_rate_all_causes', 'Annual mortality after dispersal age', p.annual_mortality, 'probability of death per year', []),
    ]
    rows = []
    for name, label, actual, units, checks in used:
        source = parameters[name]
        confidence = evidence.get(name, {})
        rows.append(dict(name=name, label=label, research_value=float(source['baseline']),
                         low=float(source['low']), high=float(source['high']),
                         research_units=source['units'], used_value=actual, used_units=units,
                         confidence=confidence.get('confidence', 'not recorded'),
                         confidence_reason=confidence.get('confidence_reason', ''),
                         evidence_note=source['evidence_or_assumption'],
                         sources=[dict(key=key, citation=sources[key]['citation'])
                                  for key in map(str.strip, source['source'].split(';'))], checks=checks))
    patches = [dict(id=patch['id'], area=patch['area_km2'],
                    female_capacity=math.floor(patch['area_km2'] / p.home_range),
                    starting_females=config['initial_population']['females'] // 2)
               for patch in config['patches']]
    return dict(run_id=config['run_id'], rows=rows, patches=patches,
                food=config['food_rabbits_per_ha'], food_threshold=p.food_threshold,
                food_allows_breeding=config['food_rabbits_per_ha'] >= p.food_threshold,
                historical_validation='not_assessed',
                outcomes=dict(starting_population=results['history'][0]['population'],
                              final_population=results['history'][-1]['population'],
                              births=sum(row['births'] for row in results['history'][1:]),
                              deaths=sum(row['deaths'] for row in results['history'][1:])))
