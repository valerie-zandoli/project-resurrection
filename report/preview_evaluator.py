"""Submit one saved preview to the existing, bounded Claude Evaluator role."""
import json
import uuid
from pathlib import Path

import jsonschema

from harness.litellm_provider import LiteLLMProvider
from harness.roles import model_evaluator
from harness.trace import Trace, scrub
from simulation.model import REPO
from validators.handoff_hashes import file_sha256


def evaluate_preview(directory, *, provider_factory=LiteLLMProvider.from_environment):
    """Read the saved run; never simulate again or revise its artifacts."""
    directory = Path(directory)
    config = json.loads((directory / 'input.json').read_text())
    results = json.loads((directory / 'results.json').read_text())
    for document, name in [(config, 'input'), (results, 'results')]:
        schema = json.loads((REPO / 'schemas' / f'{name}.schema.json').read_text())
        jsonschema.validate(document, schema)
    if config['run_id'] != directory.name or results['run_id'] != directory.name:
        raise ValueError('The saved run identity does not match its folder.')
    files = ['input.json', 'results.json', 'preview.json']
    record = json.loads((directory / 'preview.json').read_text())
    files.extend('snapshot/' + name for name in record['research_sha256'])
    hashes = {name: file_sha256(directory / name) for name in files}
    if any(hashes['snapshot/' + name] != digest
           for name, digest in record['research_sha256'].items()):
        raise ValueError('The research snapshot changed. Create a new experiment before evaluation.')
    review_id = 'review-' + uuid.uuid4().hex
    review = directory / 'reviews' / review_id
    review.mkdir(parents=True, exist_ok=False)
    trace = Trace(review / 'trace.jsonl')
    trace.input_hashes = hashes
    trace.add('harness', 'Saved preview submitted for independent artifact checks.', revision_round=0)
    try:
        provider = provider_factory()
        evaluator = model_evaluator(provider, trace=trace)
        evaluation = evaluator(config, results, directory / 'snapshot', 0)
        schema = json.loads((REPO / 'schemas/evaluation.schema.json').read_text())
        jsonschema.validate(evaluation, schema)
        if any(file_sha256(directory / name) != digest for name, digest in hashes.items()):
            raise ValueError('Saved experiment files changed during evaluation.')
        explanation, removed = scrub(evaluator.summaries[-1], limit=6000)
        report = dict(run_id=config['run_id'], review_id=review_id, evaluation=evaluation,
                      explanation=explanation, removed_text=removed, input_sha256=hashes,
                      model=getattr(provider, 'model', 'test-provider'),
                      scope='Existing artifact checks with a Claude explanation; historical validation not assessed.')
        (review / 'report.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
        trace.add('harness', 'Evaluation saved.', evaluator_status=evaluation['status'], revision_round=0)
        return dict(report, report_url=f'/runs/{config["run_id"]}/reviews/{review_id}/report.json')
    except Exception:
        # Provider error text can contain credentials; publish only a fixed failure message.
        trace.add('harness', 'Evaluator did not complete. This attempt has no accepted verdict.')
        raise
