import json

import pytest

from scripts.compare_breeding_runs import compare_batches, main, render_markdown
from simulation.experiments import run_batch


@pytest.fixture
def batches(tmp_path):
    for name, rule in [('step', 'spring_threshold'), ('linear', 'linear_food_sensitivity')]:
        report = run_batch(tmp_path / name, seed=13, trials=2, months=12, breeding_rule=rule)
        assert report['status'] == 'completed'
    return tmp_path / 'step/batch.json', tmp_path / 'linear/batch.json'


def edit(path, change):
    data = json.loads(path.read_text())
    change(data)
    path.write_text(json.dumps(data))


def trial_file(path, name):
    batch = json.loads(path.read_text())
    return path.parent / batch['cells'][0]['trials'][0]['artifacts'] / f'{name}.json'


def test_real_batches_produce_a_readable_comparison(batches):
    report = compare_batches(*batches)
    assert report['historical_validation'] == 'not_assessed'
    assert len(report['cells']) == 6 and report['trials_per_cell'] == 2
    text = render_markdown(report)
    assert 'Sudden cutoff' in text and 'Gradual rise' in text and 'percentage points' in text
    assert '95% interval' in text and 'not a statistical test' in text
    assert 'do not establish which rule' in text


@pytest.mark.parametrize('field,value', [('seed', 999), ('settlement_rule', 'one_try_at_dispersal'),
                                        ('code_sha256', {'different': 'code'})])
def test_mismatched_context_is_rejected(batches, field, value):
    edit(batches[1], lambda b: b.update({field: value}))
    with pytest.raises(ValueError, match='differ'):
        compare_batches(*batches)


def test_wrong_rule_is_rejected(batches):
    with pytest.raises(ValueError, match='Wrong breeding rule'):
        compare_batches(batches[1], batches[0])


def test_missing_or_incomplete_trials_are_rejected(batches):
    edit(batches[1], lambda b: b['cells'][0]['trials'].pop())
    with pytest.raises(ValueError, match='Incomplete cell'):
        compare_batches(*batches)


def test_changed_research_identity_cannot_be_compared(batches):
    path = trial_file(batches[1], 'input')
    edit(path, lambda c: c.update(parameters_sha256='1' * 64))
    with pytest.raises(ValueError, match='artifact checks'):
        compare_batches(*batches)


def test_forged_saved_statistics_are_rejected(batches):
    edit(batches[1], lambda b: b['cells'][0]['statistics'].update(final_population_median=99999))
    with pytest.raises(ValueError, match='Saved statistics differ'):
        compare_batches(*batches)


def test_forged_trial_summary_is_rejected(batches):
    edit(trial_file(batches[1], 'summary'), lambda s: s.update(final_population=99999))
    with pytest.raises(ValueError, match='Summary differs'):
        compare_batches(*batches)


def test_artifact_path_cannot_leave_batch(batches):
    edit(batches[1], lambda b: b['cells'][0]['trials'][0].update(artifacts='../elsewhere'))
    with pytest.raises(ValueError, match='inside its batch folder'):
        compare_batches(*batches)


def test_different_trial_seeds_rejected_even_if_each_batch_is_valid(batches):
    folder = batches[1].parent.parent / 'different-seeds'
    run_batch(folder, seed=14, trials=2, months=12, breeding_rule='linear_food_sensitivity')
    # Hide the top-level difference; per-trial seeds must still expose it.
    edit(folder / 'batch.json', lambda b: b.update(seed=13))
    with pytest.raises(ValueError, match='trial seeds differ'):
        compare_batches(batches[0], folder / 'batch.json')


def test_cli_writes_report_then_refuses_overwrite(batches, tmp_path):
    output = tmp_path / 'comparison.md'
    args = ['--threshold', str(batches[0]), '--linear', str(batches[1]), '--output', str(output)]
    assert main(args) == 0
    content = output.read_text()
    assert content.startswith('# Breeding rule comparison')
    assert main(args) == 1 and output.read_text() == content


def stats(share):
    return dict(persistence_share=share, persistence_wilson_95=[share / 2, min(1, share + .1)],
                final_population_median=10, extinction_share=0.0, extinction_month_median=None)


def test_report_puts_each_rule_in_its_own_column_and_the_difference_is_gradual_minus_cutoff():
    comparison = dict(seed=1, settlement_rule='monthly_current_then_other', trials_per_cell=10,
                      duration_months=12, historical_validation='not_assessed',
                      cells=[dict(name='c', food=2.3, area=50, threshold=stats(.2), linear=stats(.7))])
    row = next(line for line in render_markdown(comparison).splitlines() if line.startswith('| 2.3, 50'))
    columns = [part.strip() for part in row.strip('|').split('|')]
    assert columns[1].startswith('20.0%')   # sudden cutoff
    assert columns[2].startswith('70.0%')   # gradual rise
    assert columns[3].startswith('+50.0 percentage points (gradual minus cutoff)')


def test_report_from_real_batches_keeps_each_rules_numbers_and_states_the_settings(batches):
    report = compare_batches(*batches)
    step, linear = (json.loads(path.read_text()) for path in batches)
    for cell, step_cell, linear_cell in zip(report['cells'], step['cells'], linear['cells']):
        assert cell['threshold'] == step_cell['statistics'] and cell['linear'] == linear_cell['statistics']
    assert any(cell['threshold'] != cell['linear'] for cell in report['cells'])  # so a swap would show
    text = render_markdown(report)
    assert '`monthly_current_then_other`' in text and 'the same in both batches' in text
    assert '`spring_threshold`' in text and '`linear_food_sensitivity`' in text
    assert 'identical by construction' in text
    assert 'living breeding-age female holding a territory' in text and 'eligible male' not in text


def test_a_batch_made_before_the_breeding_option_is_refused_with_a_clear_message(batches):
    edit(batches[0], lambda b: b.pop('breeding_rule'))
    with pytest.raises(ValueError, match='records no breeding rule'):
        compare_batches(*batches)
