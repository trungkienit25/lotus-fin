"""Reproducible offline builder gates with command, exit, and content receipts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--node", default="node")
    parser.add_argument("--output", default="docs/reviews/evidence/p6-full-integration")
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to(ROOT):
        parser.error("Evidence must stay in this workspace")
    output.mkdir(parents=True, exist_ok=True)
    tests = ROOT / "lotus_fin/lotus_fin/tests"
    invoice = sorted(str(p.relative_to(ROOT)) for p in tests.glob("test_invoice*.py"))
    invoice += sorted(str(p.relative_to(ROOT)) for p in tests.glob("test_action*.py"))
    invoice += [str((tests / name).relative_to(ROOT)) for name in (
        "test_copilot_full_integration.py", "test_l4_mutation_security.py", "test_l5_action_workflows.py",
        "test_overdue_evaluator.py", "test_search_overdue_invoices.py", "test_disabled_user_revocation.py",
        "test_frappe_only_boundary.py")]
    frontend = sorted(str(p.relative_to(ROOT)) for p in (ROOT / "frontend/tests").rglob("*.test.ts"))
    gates = [
        ("backend", [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", *invoice], ROOT),
        ("frontend", [args.node, "--experimental-strip-types", "--test", *frontend], ROOT),
        ("types", [args.node, "node_modules/typescript/bin/tsc", "-b"], ROOT / "frontend"),
        ("build", [args.node, "node_modules/vite/bin/vite.js", "build", "--base=/assets/lotus_fin/core/"], ROOT / "frontend"),
        ("lint", [str(ROOT / "frontend/node_modules/.bin/oxlint.cmd") if os.name == "nt" else
                   str(ROOT / "frontend/node_modules/.bin/oxlint")], ROOT / "frontend"),
        ("whitespace", ["git", "diff", "--check"], ROOT),
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "lotus_fin")
    temp = output / "temp"
    temp.mkdir(exist_ok=True)
    env["TEMP"] = env["TMP"] = env["TMPDIR"] = str(temp)
    receipts = []
    for name, command, cwd in gates:
        result = subprocess.run(command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        log = output / f"{name}.txt"
        log.write_bytes(result.stdout)
        receipts.append({"gate": name, "argv": command, "cwd": str(cwd), "exit": result.returncode,
                         "output_sha256": hashlib.sha256(result.stdout).hexdigest()})
        print(f"{name}: exit {result.returncode}", flush=True)
    (output / "COMMANDS_AND_EXITS.json").write_text(json.dumps(receipts, indent=2), encoding="utf-8")
    manifest = {}
    for directory in ("frontend/src", "frontend/tests", "lotus_fin/lotus_fin", "docker/lotus-core"):
        for path in (ROOT / directory).rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and ".pytest_cache" not in path.parts:
                manifest[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    for file in ("frontend/package.json", "frontend/package-lock.json", "lotus_fin/pyproject.toml"):
        manifest[file] = hashlib.sha256((ROOT / file).read_bytes()).hexdigest()
    (output / "SOURCE_AND_TEST_HASHES.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return int(any(r["exit"] for r in receipts))


if __name__ == "__main__":
    sys.exit(main())
