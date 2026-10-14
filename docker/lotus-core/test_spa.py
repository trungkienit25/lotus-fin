"""Offline renderer tests: no framework installation, records or runtime mutation."""
import importlib.util
import pathlib
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch


class AuthenticationError(Exception):
    pass


class SpaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        self.entry = self.root / "templates/lotus_spa.html"
        self.entry.parent.mkdir()
        self.entry.write_text('<div id="root"></div>', encoding="utf-8")
        self.frappe = types.ModuleType("frappe")
        self.frappe.session = types.SimpleNamespace(user="ordinary", sid="cookie")
        self.frappe.request = types.SimpleNamespace(method="GET")
        self.frappe.AuthenticationError = AuthenticationError
        self.frappe.db = types.SimpleNamespace(commit=Mock())
        self.frappe.get_app_path = lambda app, *parts: str(self.root.joinpath(*parts))
        self.sessions = types.ModuleType("frappe.sessions")
        self.sessions.get_csrf_token = Mock(return_value="current-token")
        self.boundary = types.ModuleType("lotus_fin.runtime.boundary")
        self.boundary.validate_authenticated_principal = Mock()
        self.modules = patch.dict(sys.modules, {"frappe": self.frappe,
            "frappe.sessions": self.sessions, "lotus_fin.runtime.boundary": self.boundary})
        self.modules.start()
        source = pathlib.Path(__file__).resolve().parents[2] / "lotus_fin/lotus_fin/runtime/spa.py"
        spec = importlib.util.spec_from_file_location("p4c_spa", source)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def tearDown(self):
        self.modules.stop()
        self.temp.cleanup()

    def render(self, route="copilot"):
        return self.module.LotusSpaPage(route).render()

    def test_routes_are_qualified(self):
        for route in ("copilot", "ai", "home", "copilot/session", "/copilot/"):
            self.assertTrue(self.module.LotusSpaPage(route).can_render())
        for route in ("api/method/login", "assets/foo", "desk", "copilot/unknown", "copilot.js", ""):
            self.assertFalse(self.module.LotusSpaPage(route).can_render())

    def test_authenticated_shell_is_private(self):
        response = self.render()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'id="root"', response.data)
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.assertEqual(response.headers["Vary"], "Cookie")
        self.boundary.validate_authenticated_principal.assert_called_once_with("ordinary", "cookie")
        self.sessions.get_csrf_token.assert_not_called()

    def test_guest_redirects_without_reading_private_shell(self):
        self.frappe.session.user = "Guest"
        self.entry.unlink()
        response = self.render()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/login?redirect-to=%2Fcopilot")
        self.assertNotIn(b"root", response.data)

    def test_guest_bootstrap_is_401_not_redirect(self):
        self.frappe.session.user = "Guest"
        response = self.render("copilot/session")
        self.assertEqual(response.status_code, 401)
        self.assertNotIn(b"csrf_token", response.data)
        self.sessions.get_csrf_token.assert_not_called()

    def test_bootstrap_uses_framework_session_and_commits(self):
        response = self.render("copilot/session")
        self.assertEqual(response.json, {"user": "ordinary", "csrf_token": "current-token"})
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.sessions.get_csrf_token.assert_called_once()
        self.frappe.db.commit.assert_called_once()

    def test_disabled_or_revoked_principal_is_denied(self):
        self.boundary.validate_authenticated_principal.side_effect = AuthenticationError
        for route in ("copilot", "copilot/session"):
            response = self.render(route)
            self.assertEqual(response.status_code, 401)
            self.assertNotIn(b"csrf_token", response.data)
        self.sessions.get_csrf_token.assert_not_called()

    def test_missing_cookie_is_denied(self):
        self.frappe.session.sid = None
        self.assertEqual(self.render("copilot/session").status_code, 401)

    def test_missing_build_is_truthful_503(self):
        self.entry.unlink()
        self.assertEqual(self.render().status_code, 503)

    def test_post_never_mints_session_tokens(self):
        self.frappe.request.method = "POST"
        response = self.render("copilot/session")
        self.assertEqual(response.status_code, 405)
        self.sessions.get_csrf_token.assert_not_called()


if __name__ == "__main__":
    unittest.main()
