"""Explicit project ownership and one implementation for Windows/POSIX helpers."""
import argparse
import hashlib
import json
import os
import pathlib
import re
import secrets
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
COMPOSE = ROOT / 'docker/compose.lotus-core.yml'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['build', 'setup', 'smoke', 'status', 'health',
                                           'logs', 'cleanup', 'help'])
    parser.add_argument('--project')
    parser.add_argument('--site')
    parser.add_argument('--port', type=int, default=8097)
    parser.add_argument('--authorize-isolated', metavar='EXACT_PROJECT')
    args = parser.parse_args()
    if args.command == 'help':
        parser.print_help()
        return 0
    if not args.project or not re.fullmatch(r'lotus-core-[a-z0-9][a-z0-9-]{2,40}', args.project):
        parser.error('Explicit isolated project lotus-core-<id> required')
    suffix = args.project[len('lotus-core-'):]
    site = args.site or f'core-{suffix}.localhost'
    if site != f'core-{suffix}.localhost' or not 1024 <= args.port <= 65535:
        parser.error('Site must match the isolated project; port must be 1024..65535')
    image = f'lotus-fin:core-{suffix}'
    env = os.environ.copy()
    # Do not inherit Compose overrides/project/site selection from a shared shell.
    for key in list(env):
        if key.startswith(('COMPOSE_', 'LOTUS_')):
            env.pop(key)
    def call(argv, capture=False):
        result = subprocess.run(argv, cwd=ROOT, env=env, text=True,
                                stdout=subprocess.PIPE if capture else None, check=False)
        if result.returncode:
            raise SystemExit(result.returncode)
        return result.stdout.strip() if capture else ''
    if args.command == 'build':
        call(['docker', 'build', '--progress', 'plain', '-f',
              str(ROOT / 'docker/lotus-core/Dockerfile'), '-t', image, str(ROOT)])
        return 0
    state = ROOT / '.runtime' / args.project
    owner = state / 'owner.json'
    envfile = state / 'core.env'
    identity = {'project': args.project, 'site': site, 'port': args.port,
                'compose_sha256': hashlib.sha256(COMPOSE.read_bytes()).hexdigest()}
    if args.command in ('setup', 'cleanup') and args.authorize_isolated != args.project:
        parser.error('Mutation requires --authorize-isolated with the exact project')
    if not owner.exists():
        if args.command != 'setup':
            parser.error('No owned project; run explicitly authorized setup first')
        existing = call(['docker', 'ps', '-aq', '--filter',
                         f'label=com.docker.compose.project={args.project}'], True)
        volumes = call(['docker', 'volume', 'ls', '-q', '--filter',
                        f'label=com.docker.compose.project={args.project}'], True)
        # Also refuse name collisions whose Compose label is absent/different.
        named = call(['docker', 'volume', 'ls', '-q', '--filter',
                      f'name=^{args.project}_'], True)
        if existing or volumes or named:
            parser.error('Refusing to adopt an existing project or volume')
        state.mkdir(parents=True, exist_ok=False)
        owner.write_text(json.dumps(identity, indent=2), encoding='utf-8')
        envfile.write_text(f'LOTUS_PROJECT={args.project}\nLOTUS_SITE={site}\n'
                           f'LOTUS_IMAGE={image}\nLOTUS_PORT={args.port}\n'
                           f'LOTUS_DB_PASSWORD={secrets.token_urlsafe(36)}\n'
                           f'LOTUS_ADMIN_PASSWORD={secrets.token_urlsafe(36)}\n', encoding='utf-8')
        if os.name != 'nt':
            envfile.chmod(0o600)
    if json.loads(owner.read_text(encoding='utf-8')) != identity:
        parser.error('Ownership/site/port/recipe mismatch; use a new isolated project')
    prefix = ['docker', 'compose', '--project-name', args.project, '--env-file',
              str(envfile), '-f', str(COMPOSE)]
    if args.command == 'setup':
        call(prefix + ['up', '-d', '--wait', '--wait-timeout', '240'])
    elif args.command == 'cleanup':
        # Deliberately retain volumes. No volume-removal command is provided.
        call(prefix + ['down', '--timeout', '30'])
    elif args.command == 'logs':
        call(prefix + ['logs', '--tail', '100'])
    elif args.command == 'status':
        call(prefix + ['ps', '-a'])
    else:
        call(prefix + ['exec', '-T', 'backend', 'env/bin/python',
                       '/home/frappe/lotus-core/smoke.py'])
        import urllib.request
        with urllib.request.urlopen(f'http://127.0.0.1:{args.port}/api/method/ping', timeout=10) as response:
            if response.status != 200 or json.load(response).get('message') != 'pong':
                raise SystemExit('Framework HTTP readiness failed')
        print('Framework HTTP readiness PASS; financial capabilities remain unqualified')
    return 0


if __name__ == '__main__':
    sys.exit(main())
