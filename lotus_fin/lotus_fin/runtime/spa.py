"""Qualified same-origin React serving through Frappe's website renderer."""
import json
from pathlib import Path

import frappe
from frappe.sessions import get_csrf_token
from werkzeug.wrappers import Response

from lotus_fin.runtime.boundary import validate_authenticated_principal


class LotusSpaPage:
    """Only explicit React routes are eligible; API/assets/Desk keep their handlers."""

    ROUTES = frozenset({"copilot", "ai", "home"})
    BOOTSTRAP = "copilot/session"
    HEADERS = {
        "Cache-Control": "private, no-store, max-age=0",
        "Vary": "Cookie",
        "X-Content-Type-Options": "nosniff",
    }

    def __init__(self, path, http_status_code=None):
        self.path = path.strip("/")

    def can_render(self):
        return self.path in self.ROUTES or self.path == self.BOOTSTRAP

    def render(self):
        if frappe.request.method != "GET":
            return Response(status=405, headers={**self.HEADERS, "Allow": "GET"})
        user = frappe.session.user
        sid = frappe.session.sid
        if user == "Guest" or not sid or sid == "Guest":
            if self.path == self.BOOTSTRAP:
                return Response('{"exc_type":"AuthenticationError"}', status=401,
                                mimetype="application/json", headers=self.HEADERS)
            return Response(status=302, headers={**self.HEADERS,
                "Location": "/login?redirect-to=%2Fcopilot"})

        # Reuse Backend Security's persisted principal/session enforcement.
        try:
            validate_authenticated_principal(user, sid)
        except frappe.AuthenticationError:
            return Response('{"exc_type":"AuthenticationError"}', status=401,
                            mimetype="application/json", headers=self.HEADERS)
        if self.path == self.BOOTSTRAP:
            token = get_csrf_token()
            # Desk documents the commit requirement: token generation forces a
            # session update; GET requests otherwise do not commit DB writes.
            frappe.db.commit()
            return Response(json.dumps({"user": user, "csrf_token": token}),
                            mimetype="application/json", headers=self.HEADERS)

        entry = Path(frappe.get_app_path("lotus_fin", "templates", "lotus_spa.html"))
        if not entry.is_file():
            return Response("Lotus application build unavailable", status=503,
                            mimetype="text/plain", headers=self.HEADERS)
        return Response(entry.read_text(encoding="utf-8"), mimetype="text/html",
                        headers=self.HEADERS)
