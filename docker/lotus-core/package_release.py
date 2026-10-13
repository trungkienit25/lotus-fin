"""Copy exact selected working-tree bytes; verify a deterministic source archive."""
import argparse
import ast
import gzip
import hashlib
import io
import json
import pathlib
import re
import subprocess
import tarfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
EXCLUDE_PARTS = {'.git', '.gitnexus', '.zcode', '.zcodeignore', 'node_modules', '__pycache__',
                 '.pytest_cache', 'dist', '.runtime', '.venv'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = pathlib.Path(args.output).resolve()
    if not output.is_relative_to(ROOT) or output.exists():
        parser.error('Output must be a NEW directory inside this workspace')
    selected = set()
    # Accepted-source baseline includes native contracts and test support/docs.
    baseline = ROOT / 'docs/reviews/evidence/chatbot-release-candidate-2026-10-13-01a132c2/SOURCE_MANIFEST.json'
    for entry in json.loads(baseline.read_text(encoding='utf-8'))['files']:
        if (ROOT / entry['path']).is_file():
            selected.add(entry['path'])
    for directory in ('lotus_fin', 'frontend', 'docker', 'integrations', 'tests_e2e'):
        for path in (ROOT / directory).rglob('*'):
            rel = path.relative_to(ROOT)
            if path.is_file() and not (set(rel.parts) & EXCLUDE_PARTS):
                if path.suffix not in ('.pyc', '.log', '.tsbuildinfo') and path.name != '_run.txt':
                    selected.add(rel.as_posix())
    selected.update(['AGENTS.md', 'README.md', 'run.ps1', 'run.sh', '.gitignore', '.gitattributes',
                     'docs/security/LotusFin_Security_SSOT_Code_V3_Codebase_Aligned.md'])
    rows, findings = [], []
    for name in sorted(selected):
        path = pathlib.PurePosixPath(name)
        if set(path.parts) & EXCLUDE_PARTS or (path.name.startswith('.env') and path.name != '.env.example'):
            continue
        source = ROOT / name
        data = source.read_bytes()
        if source.suffix == '.py':
            ast.parse(data, filename=name)  # Syntax validation without cache mutation.
        # Concrete credential formats only; never emit candidate values.
        for pattern in (rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
                        rb'AKIA[0-9A-Z]{16}', rb'AIza[0-9A-Za-z_-]{35}',
                        rb'gh[pousr]_[A-Za-z0-9]{36,}', rb'sk-proj-[A-Za-z0-9_-]{40,}'):
            if re.search(pattern, data):
                findings.append({'path': name, 'kind': 'credential_format'})
        rows.append({'path': name, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
    if findings:
        raise SystemExit('Credential-format findings in selected source: ' + json.dumps(findings))
    output.mkdir(parents=True)
    candidate = output / 'candidate'
    tar_bytes = io.BytesIO()
    with tarfile.open(fileobj=tar_bytes, mode='w', format=tarfile.PAX_FORMAT) as archive:
        for entry in rows:
            name = entry['path']
            data = (ROOT / name).read_bytes()
            assert hashlib.sha256(data).hexdigest() == entry['sha256'], 'Source changed during packaging'
            target = candidate / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            assert hashlib.sha256(target.read_bytes()).hexdigest() == entry['sha256']
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o755 if name.endswith('.sh') else 0o644
            info.mtime = 0
            archive.addfile(info, io.BytesIO(data))
    compressed = gzip.compress(tar_bytes.getvalue(), mtime=0)
    (output / 'LOTUS_CORE_SOURCE.tar.gz').write_bytes(compressed)
    with tarfile.open(fileobj=io.BytesIO(compressed), mode='r:gz') as archive:
        assert len(archive.getmembers()) == len(rows)
        for entry in rows:
            assert hashlib.sha256(archive.extractfile(entry['path']).read()).hexdigest() == entry['sha256']
    manifest = {'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'source': 'current working tree, including approved dirty/untracked source; not HEAD',
                'files': rows}
    manifest_data = (json.dumps(manifest, indent=2) + '\n').encode()
    (output / 'SOURCE_MANIFEST.json').write_bytes(manifest_data)
    summary = {'files': len(rows), 'transfer_verified': len(rows), 'archive_verified': len(rows),
        'python_syntax_files': sum(entry['path'].endswith('.py') for entry in rows),
        'archive_sha256': hashlib.sha256(compressed).hexdigest(),
        'manifest_sha256': hashlib.sha256(manifest_data).hexdigest(),
        'credential_format_findings': findings,
        'secret_scan_limit': 'Concrete patterns only; does not prove absence of every possible secret'}
    (output / 'INTEGRITY.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
