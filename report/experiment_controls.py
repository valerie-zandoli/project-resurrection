"""Serve a local form for saved, single-run synthetic simulator previews."""

import argparse
import hmac
import json
import math
import platform
import re
import secrets
import shutil
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import jsonschema

from harness.snapshot import make_snapshot
from report.lynx_viewer import render_viewer
from report.preview_evaluator import evaluate_preview
from harness.litellm_provider import LiteLLMProvider, DEFAULT_ENV_FILE
from simulation.model import REPO, load_parameters, preview_config, simulate, summary, validate_config
from validators.evidence_gate import check_repository
from validators.handoff_hashes import file_sha256

LIMITS = {
    'food': (0, 100), 'area': (1, 1000), 'months': (1, 120),
    'population': (4, 200), 'seed': (0, 2**32 - 1),
}
INTEGER_FIELDS = {'months', 'population', 'seed'}
ARTIFACTS = {'viewer.html', 'input.json', 'results.json', 'summary.json', 'preview.json'}


def validate_settings(settings):
    """Bound work and accept only the controls this page actually exposes."""
    if not isinstance(settings, dict) or set(settings) != set(LIMITS):
        raise ValueError('Provide food, area, months, population and seed only.')
    for name, (low, high) in LIMITS.items():
        value = settings[name]
        if type(value) not in (int, float) or (type(value) is float and not math.isfinite(value)):
            raise ValueError(f'{name}: enter a finite number.')
        if name in INTEGER_FIELDS and type(value) is not int:
            raise ValueError(f'{name}: enter a whole number.')
        if not low <= value <= high:
            raise ValueError(f'{name}: choose a value from {low} to {high}.')
    if settings['population'] % 4:
        raise ValueError('Starting lynxes must be a multiple of 4 for an equal split by sex and patch.')
    return dict(settings)


def run_experiment(settings, output_root, source_root=REPO):
    """Reuse the fixed simulator, preserve research copies, and never overwrite a run."""
    settings = validate_settings(settings)
    run_id = 'interactive-' + uuid.uuid4().hex
    directory = Path(output_root) / run_id
    directory.mkdir(parents=True, exist_ok=False)
    try:
        snapshot = directory / 'snapshot'
        hashes = make_snapshot(source_root, snapshot)  # copies, locks, and hashes the evidence file too (#100)
        errors, evidence_report = check_repository(snapshot, 'pilot')
        if errors:
            raise ValueError('The research evidence check stopped the preview: ' + '; '.join(errors))
        config = preview_config(settings['seed'], settings['months'], settings['food'],
                                settings['area'], root=snapshot)
        config['run_id'] = run_id
        config['initial_population'].update(
            females=settings['population'] // 2, males=settings['population'] // 2)
        parameters = load_parameters(config, snapshot)
        try:
            validate_config(config, parameters)
        except ValueError as error:
            if 'territory capacity' in str(error):
                raise ValueError('There is not enough territory for that starting population. '
                                 'Increase the area per patch or start with fewer lynxes.') from error
            raise
        result = simulate(config, root=snapshot)
        report = summary(result)
        html = render_viewer(result)
        record = dict(purpose='interactive_synthetic_preview', stage='pilot',
                      historical_validation='not_assessed', settings=settings,
                      research_sha256=hashes, evidence=evidence_report,
                      python_version=platform.python_version(),
                      model_sha256=file_sha256(REPO / 'simulation/model.py'))
        for name, data in [('input', config), ('results', result), ('summary', report), ('preview', record)]:
            (directory / f'{name}.json').write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')
        (directory / 'viewer.html').write_text(html, encoding='utf-8')
        return dict(run_id=run_id, summary=report, settings=settings, evidence=evidence_report,
                    viewer_url=f'/runs/{run_id}/viewer.html',
                    results_url=f'/runs/{run_id}/results.json',
                    input_url=f'/runs/{run_id}/input.json',
                    record_url=f'/runs/{run_id}/preview.json')
    except Exception:
        # Only this freshly allocated, incomplete run may be removed.
        shutil.rmtree(directory)
        raise


class PreviewServer(ThreadingHTTPServer):
    """Loopback only; no arbitrary filesystem routes or remote-triggered runs."""

    def __init__(self, port, output_root, source_root=REPO, *, env_file=DEFAULT_ENV_FILE,
                 provider_factory=None):
        self.output_root = Path(output_root)
        self.source_root = Path(source_root)
        self.token = secrets.token_urlsafe(32)
        self.busy = threading.Lock()
        self.completed = set()
        self.reviews = {}
        self.review_attempts = {}
        self.provider_factory = provider_factory or (lambda: LiteLLMProvider.from_environment(env_file=env_file))
        super().__init__(('127.0.0.1', port), PreviewHandler)

    @property
    def origin(self):
        return f'http://127.0.0.1:{self.server_port}'


class PreviewHandler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def respond(self, status, body, content_type='application/json; charset=utf-8'):
        if not isinstance(body, bytes):
            body = json.dumps(body, allow_nan=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy',
                         "default-src 'self'; script-src 'self' 'unsafe-inline'; "
                         "style-src 'self' 'unsafe-inline'; frame-ancestors 'self'; "
                         "base-uri 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(body)

    def correct_host(self):
        return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'

    def do_GET(self):
        if not self.correct_host():
            self.respond(403, {'error': 'Open the local address printed by the server.'})
            return
        if self.path == '/':
            template = Path(__file__).with_name('experiment_controls.html').read_text(encoding='utf-8')
            self.respond(200, template.replace('__SESSION_TOKEN__', self.server.token).encode('utf-8'),
                         'text/html; charset=utf-8')
            return
        match = re.fullmatch(r'/runs/(interactive-[a-f0-9]{32})/([a-z.]+)', self.path)
        if match and match[1] in self.server.completed and match[2] in ARTIFACTS:
            file = self.server.output_root / match[1] / match[2]
            content_type = 'text/html; charset=utf-8' if file.suffix == '.html' else 'application/json; charset=utf-8'
            self.respond(200, file.read_bytes(), content_type)
            return
        review = re.fullmatch(r'/runs/(interactive-[a-f0-9]{32})/reviews/(review-[a-f0-9]{32})/report.json', self.path)
        if review and review[1] in self.server.reviews:
            result = self.server.reviews[review[1]]
            if review[2] == result['review_id']:
                self.respond(200, result)
                return
        self.respond(404, {'error': 'Preview file not found.'})

    def do_POST(self):
        if (not self.correct_host() or self.headers.get('Origin') != self.server.origin
                or not hmac.compare_digest(self.headers.get('X-Experiment-Token', '').encode('utf-8'), self.server.token.encode('utf-8'))):
            self.respond(403, {'error': 'Refresh the local experiment page before running.'})
            return
        evaluation_request = re.fullmatch(r'/api/runs/(interactive-[a-f0-9]{32})/evaluate', self.path)
        if self.path != '/api/runs' and not evaluation_request:
            self.respond(404, {'error': 'Unknown action.'})
            return
        if (self.headers.get('Content-Type') != 'application/json'
                or self.headers.get('Transfer-Encoding')):
            self.respond(415, {'error': 'Use a JSON request.'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            length = 0
        if not 0 < length <= 2048:
            self.respond(413, {'error': 'The settings request must be between 1 and 2048 bytes.'})
            return
        try:
            settings = json.loads(self.rfile.read(length))
            if evaluation_request:
                if settings != {}:
                    raise ValueError('Evaluation takes only the saved run, with no overrides.')
            else:
                validate_settings(settings)
        except (ValueError, UnicodeDecodeError, OverflowError):
            self.respond(400, {'error': 'Check the numbers and supported ranges in the form.'})
            return
        if not self.server.busy.acquire(blocking=False):
            self.respond(409, {'error': 'An experiment or evaluation is already running. Please wait.'})
            return
        try:
            if evaluation_request:
                self.evaluate_saved(evaluation_request[1])
                return
            if len(self.server.completed) >= 100:
                self.respond(429, {'error': 'This session has saved 100 previews. Restart the server to continue.'})
                return
            result = run_experiment(settings, self.server.output_root, self.server.source_root)
            self.server.completed.add(result['run_id'])
            self.respond(201, result)
        except (ValueError, jsonschema.ValidationError) as error:
            self.respond(422, {'error': str(error)[:600]})
        except Exception:
            self.log_error('Preview failed; no completed result was published.')
            self.respond(500, {'error': 'The preview could not finish. Check the research files and output folder.'})
        finally:
            self.server.busy.release()

    def evaluate_saved(self, run_id):
        if run_id not in self.server.completed:
            self.respond(404, {'error': 'Choose a completed experiment from this session.'})
            return
        if run_id in self.server.reviews:
            self.respond(200, self.server.reviews[run_id])
            return
        attempts = self.server.review_attempts.get(run_id, 0)
        if attempts >= 3:
            self.respond(429, {'error': 'Three evaluation attempts have been used. Check the saved diagnostics before continuing.'})
            return
        self.server.review_attempts[run_id] = attempts + 1
        try:
            result = evaluate_preview(self.server.output_root / run_id,
                                      provider_factory=self.server.provider_factory)
            self.server.reviews[run_id] = result
            self.respond(201, result)
        except Exception:
            self.respond(502, {'error': 'The Evaluator did not complete; no verdict was accepted. Check the local Claude key, model setting and connection. Your experiment is still saved.'})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='folder for new, individually named runs')
    parser.add_argument('--port', type=int, default=8767)
    parser.add_argument('--env-file', type=Path, default=DEFAULT_ENV_FILE,
                        help='local ignored key file for Claude evaluation; never copied into runs')
    args = parser.parse_args(argv)
    with PreviewServer(args.port, args.output, env_file=args.env_file) as server:
        print(f'Open {server.origin}/ — simulation is local; Send to Evaluator calls Claude. Ctrl+C to stop.', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
