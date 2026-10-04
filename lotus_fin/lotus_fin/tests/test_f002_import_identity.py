"""
Order-independent import identity tests for F002 (architecture-refactor
remediation R5).

`lotus_fin.modules.f002_cashflow.*` is the single canonical module identity.
The legacy `lotus_fin.cashflow.*` spelling must resolve to the SAME module
objects — never a second execution of the canonical files — in every import
order, so module-level state (e.g. the AI002 cache store) is shared and
dataclass/isinstance identity holds across both spellings.
"""

import os
import subprocess
import sys
import unittest

APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

IDENTITY_SNIPPET = """
import json
import sys
sys.path.insert(0, {app_root!r})

{imports}

result = {{
    "cache_identity": sys.modules["lotus_fin.cashflow.cache"] is sys.modules["lotus_fin.modules.f002_cashflow.cache"],
    "service_identity": sys.modules["lotus_fin.cashflow.service"] is sys.modules["lotus_fin.modules.f002_cashflow.service"],
    "adapters_identity": sys.modules["lotus_fin.cashflow.adapters"] is sys.modules["lotus_fin.modules.f002_cashflow.adapters"],
    "models_identity": sys.modules["lotus_fin.cashflow.models"] is sys.modules["lotus_fin.modules.f002_cashflow.models"],
    "plugin_alias": sys.modules["lotus_fin.cashflow.plugin"] is sys.modules["lotus_fin.modules.f002_cashflow.plugin"],
    "shared_cache_store": sys.modules["lotus_fin.cashflow.cache"]._CACHE_STORE is sys.modules["lotus_fin.modules.f002_cashflow.cache"]._CACHE_STORE,
    "request_class_identity": sys.modules["lotus_fin.cashflow.models"].ForecastRequest is sys.modules["lotus_fin.modules.f002_cashflow.models"].ForecastRequest,
}}
print(json.dumps(result))
"""


def _run_snippet(imports):
    code = IDENTITY_SNIPPET.format(app_root=APP_ROOT, imports=imports)
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise AssertionError(f"identity snippet failed:\n{proc.stderr}")
    return json_loads(proc.stdout)


def json_loads(text):
    import json

    return json.loads(text.strip().splitlines()[-1])


class TestF002CanonicalModuleIdentity(unittest.TestCase):
    """R5: one canonical module identity; no independent module objects/state."""

    def _assert_all_true(self, result):
        for key, value in result.items():
            self.assertTrue(value, f"{key} must be True, got {value!r}")

    def test_identity_when_legacy_imported_first(self):
        self._assert_all_true(_run_snippet(
            "import lotus_fin.cashflow.cache, lotus_fin.cashflow.service, "
            "lotus_fin.cashflow.adapters, lotus_fin.cashflow.models, lotus_fin.cashflow.plugin; "
            "import lotus_fin.modules.f002_cashflow.cache, lotus_fin.modules.f002_cashflow.service, "
            "lotus_fin.modules.f002_cashflow.adapters, lotus_fin.modules.f002_cashflow.models, "
            "lotus_fin.modules.f002_cashflow.plugin"
        ))

    def test_identity_when_canonical_imported_first(self):
        self._assert_all_true(_run_snippet(
            "import lotus_fin.modules.f002_cashflow.cache, lotus_fin.modules.f002_cashflow.service, "
            "lotus_fin.modules.f002_cashflow.adapters, lotus_fin.modules.f002_cashflow.models, "
            "lotus_fin.modules.f002_cashflow.plugin; "
            "import lotus_fin.cashflow.cache, lotus_fin.cashflow.service, "
            "lotus_fin.cashflow.adapters, lotus_fin.cashflow.models, lotus_fin.cashflow.plugin"
        ))

    def test_identity_when_package_alias_imported_first(self):
        self._assert_all_true(_run_snippet(
            "import lotus_fin.cashflow; "
            "import lotus_fin.cashflow.cache, lotus_fin.modules.f002_cashflow.cache"
        ))

    def test_cache_state_shared_across_spellings(self):
        """A store entry written via the legacy path must be visible via the
        canonical path — the AI002 cache is a single process-wide store."""
        code = (
            "import sys\n"
            f"sys.path.insert(0, {APP_ROOT!r})\n"
            "from lotus_fin.cashflow.cache import _CACHE_STORE\n"
            "_CACHE_STORE['probe-key'] = 'probe-value'\n"
            "from lotus_fin.modules.f002_cashflow.cache import _CACHE_STORE as canonical\n"
            "import json\n"
            "print(json.dumps({'visible': canonical.get('probe-key') == 'probe-value'}))\n"
        )
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(json_loads(proc.stdout)["visible"])

    def test_from_import_binds_canonical_class(self):
        """from lotus_fin.cashflow.models import ForecastRequest yields the
        canonical class (isinstance-safe across both spellings)."""
        code = (
            "import sys\n"
            f"sys.path.insert(0, {APP_ROOT!r})\n"
            "from lotus_fin.cashflow.models import ForecastRequest as legacy_cls\n"
            "from lotus_fin.modules.f002_cashflow.models import ForecastRequest as canonical_cls\n"
            "import json\n"
            "print(json.dumps({'same_class': legacy_cls is canonical_cls}))\n"
        )
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(json_loads(proc.stdout)["same_class"])


if __name__ == "__main__":
    unittest.main()
