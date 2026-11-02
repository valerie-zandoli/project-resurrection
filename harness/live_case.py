"""Run one synthetic role workflow through Claude, preserving code verdicts."""

import argparse
import contextlib
import hashlib
import io
import json
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from harness.litellm_provider import DEFAULT_ENV_FILE, LiteLLMProvider
from harness.provider import ProviderError
from harness.roles import load_prompt
from harness.run_case import HarnessError
from harness.three_role_preview import run_three_role_case
from harness.trace import Trace
from simulation.model import REPO

MAX_CALLS = 12
ROLES = ('researcher', 'developer', 'evaluator')


class CallBudget:
    def __init__(self, limit):
        self.limit = limit
        self.attempted = 0
        self.completed = {role: 0 for role in ROLES}

    def take(self):
        if self.attempted >= self.limit:
            raise ProviderError('live case model-call limit reached; no automatic retry')
        self.attempted += 1


class RecordedProvider:
    """Log scrubbed request/reply summaries, never provider objects or credentials."""
    def __init__(self, role, provider, budget, trace):
        self.role, self.provider, self.budget, self.trace = role, provider, budget, trace
        self.prompt_version = load_prompt(role)[0]

    def complete(self, system, messages, tools):
        self.budget.take()
        self.trace.add(self.role, 'model request started',
                       tool_args=dict(system=system, messages=messages, allowed_tools=list(tools)),
                       prompt_version=self.prompt_version)
        try:
            reply = self.provider.complete(system, messages, tools)
        except Exception as exc:
            # Raw provider exceptions can hold request headers or credentials.  A ProviderError's own text is already
            # scrubbed (the adapter keeps only the class name of what it caught), so it is kept:  it says why.
            reason = str(exc) if isinstance(exc, ProviderError) else type(exc).__name__
            self.trace.add(self.role, f'model request failed ({reason})', prompt_version=self.prompt_version)
            raise ProviderError(f'live {self.role} request failed ({reason})') from None
        self.budget.completed[self.role] += 1
        self.trace.add(self.role, reply['text'], tool_result=dict(tool_calls=reply['tool_calls']),
                       prompt_version=self.prompt_version)
        return reply


def evidence_read_line(check):
    """One readable line for the code-graded evidence question (see docs/live-workflow.md)."""
    if check is None:
        return 'Evidence read check (graded by code): not run, because the Researcher did not finish.'
    if check['pass']:
        return ('Evidence read check (graded by code): pass '
                '(every low row and every recorded conflict named, none invented).')
    parts = [] if check['answered'] else ['a LOW or CONFLICTS line is missing']
    parts += [f"{label} {kind}: {', '.join(check[label][kind])}"
              for label in ('low', 'conflicts') for kind in ('missing', 'invented') if check[label][kind]]
    return 'Evidence read check (graded by code): fail (' + '; '.join(parts) + ').'


def run_live_case(output, *, options, env_file=DEFAULT_ENV_FILE, model=None,
                  source_root=REPO, provider_factory=None, max_calls=MAX_CALLS):
    """Run with one fresh provider/conversation per role and a shared finite budget.

    provider_factory is an injection point for offline tests; those runs are
    explicitly labeled injected_provider_test, never live Claude evidence.
    """
    output = Path(output)
    if output.exists():
        raise HarnessError('output folder already exists; use a new one')
    if type(max_calls) is not int or not 1 <= max_calls <= 36:
        raise HarnessError('model-call limit must be an integer from 1 to 36')
    injected = provider_factory is not None
    budget = CallBudget(max_calls)
    trace = Trace(output / 'model-calls.jsonl')
    providers, models = {}, {}
    for role in ROLES:
        provider = (provider_factory(role) if injected else
                    LiteLLMProvider.from_environment(env_file=env_file))
        if model is not None and not injected:
            if not model.startswith('anthropic/claude-'):
                raise HarnessError('model must be an Anthropic Claude model')
            provider.model = model
        models[role] = getattr(provider, 'model', 'injected_test_provider')
        providers[role] = RecordedProvider(role, provider, budget, trace)

    # Provider diagnostics stay out of terminal output; only our scrubbed logs persist.
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        result = run_three_role_case(output, providers=providers, options=options,
                                     source_root=source_root)
    try:
        evidence_check = json.loads(
            (output / 'round_0' / 'researcher.json').read_text(encoding='utf-8')).get('evidence_check')
    except (OSError, ValueError):
        evidence_check = None
    try:
        adapter_version = version('litellm')
    except PackageNotFoundError:
        adapter_version = 'not_installed'
    files = ['harness/live_case.py', 'harness/roles.py', 'harness/litellm_provider.py',
             'harness/three_role_preview.py', 'harness/run_case.py', 'simulation/model.py',
             'validators/results_checks.py'] + [f'prompts/{role}.md' for role in ROLES]
    metadata = dict(
        mode='injected_provider_test' if injected else 'live_claude_attempt',
        status=result.status, reason=result.reason, models=models, litellm_version=adapter_version,
        model_calls_attempted=budget.attempted, model_calls_completed=budget.completed,
        max_model_calls=max_calls, options=options,
        all_roles_received_model_replies=all(budget.completed.values()),
        evidence_read_check=evidence_check,
        historical_validation='not_assessed',
        code_sha256={name: hashlib.sha256((REPO / name).read_bytes()).hexdigest() for name in files},
    )
    (output / 'live.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    lines = ['# Live workflow record', '', f"Mode: {metadata['mode']}",
             f'Status: {result.status}', f'Reason: {result.reason}',
             f"Duration: {options['months']} synthetic months; seed: {options['seed']}.",
             f'Model calls attempted: {budget.attempted} of {max_calls}.', '',
             '| Role | Model | Completed requests |', '|---|---|---|']
    lines += [f'| {role} | {models[role]} | {budget.completed[role]} |' for role in ROLES]
    lines += ['', evidence_read_line(evidence_check), '',
              'The numerical simulator and code checks provide the authoritative results.',
              'Researcher inspects existing tables; full scientific evidence review is not demonstrated.',
              'Developer calls a fixed simulator and does not generate or repair code.',
              'Historical validation: not assessed. This is a small integration run, not a final experiment.', '']
    (output / 'live-summary.md').write_text('\n'.join(lines), encoding='utf-8')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview', action='store_true', required=True)
    parser.add_argument('--live', action='store_true', required=True, help='send real paid Claude requests')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--env', type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument('--model', help='optional model override, recorded in live.json')
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--months', type=int, default=12)
    parser.add_argument('--food', type=float, default=4.6)
    parser.add_argument('--area', type=float, default=50)
    args = parser.parse_args(argv)
    try:
        result = run_live_case(args.output, env_file=args.env, model=args.model,
                               options=dict(seed=args.seed, months=args.months,
                                            food=args.food, area=args.area))
    except (HarnessError, ProviderError, OSError) as exc:
        print(f'Live case could not start ({type(exc).__name__}); check local setup.')
        return 2
    print(f'Live case {result.status}. Saved record: {args.output / "live-summary.md"}')
    return 0 if result.status == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
