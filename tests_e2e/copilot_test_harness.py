import subprocess
import time
import os
import socket
import shutil
import urllib.request
from urllib.parse import urlsplit, parse_qsl, unquote
from typing import Optional, Callable, List, Dict, Any

FIXTURE_URL = "http://127.0.0.1:5188"
PORT = 5188
ORIGIN = f"http://127.0.0.1:{PORT}"
COPILOT_PATH = "/api/method/lotus_fin.api.copilot_api.chat_copilot"
SESSION_PATH = "/copilot/session"
INVOICE_PATHS = (
    "/api/method/lotus_fin.api.copilot_api.invoice_context",
    "/api/method/lotus_fin.api.copilot_api.invoice_search",
    "/api/method/lotus_fin.api.copilot_api.invoice_open",
    "/api/method/lotus_fin.api.invoice_actions_api.get_context",
    "/api/method/lotus_fin.api.invoice_actions_api.search_invoices",
    "/api/method/lotus_fin.api.invoice_actions_api.open_invoice",
)
COMPANY_PATH = "/api/resource/Company"
STATIC_EXTENSIONS = (".js", ".mjs", ".ts", ".tsx", ".css", ".html", ".svg", ".png", ".json", ".map")

def is_port_in_use(port: int = PORT) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0

def get_port_listeners(port: int = PORT) -> List[int]:
    try:
        out = subprocess.check_output(["netstat", "-ano", "-p", "tcp"], stderr=subprocess.DEVNULL).decode("ascii", errors="ignore")
    except Exception:
        return []
    pids = set()
    for line in out.splitlines():
        parts = line.strip().split()
        if len(parts) >= 5 and parts[0].upper() == "TCP" and parts[3].upper() == "LISTENING" and parts[1].endswith(f":{port}"):
            if parts[4].isdigit():
                pids.add(int(parts[4]))
    return list(pids)

def kill_process_cleanly(proc: Optional[subprocess.Popen]) -> None:
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)

ROOT_DIR = os.path.normcase(os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))
_OWNED_VITE_WS_TOKEN: Optional[str] = None

def get_owned_vite_ws_token() -> Optional[str]:
    try:
        req = urllib.request.Request(f"{FIXTURE_URL}/@vite/client")
        with urllib.request.urlopen(req, timeout=1) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            # Vite injects: const wsToken = "<token>";
            marker = 'const wsToken = "'
            if marker in content:
                return content.split(marker)[1].split('"')[0]
    except Exception:
        pass
    return None

def is_allowed_static_asset(method: str, path: str, query: str) -> bool:
    if method != "GET":
        return False
    p = unquote(path)
    if not p.startswith("/"):
        return False
    if p in ("/", "/index.html", "/main.tsx", "/@vite/client"):
        return True
    if p.startswith("/.vite/deps/"):
        if not (p.endswith(".js") or p.endswith(".map")):
            return False
        if not query:
            return True
        qs = parse_qsl(query, keep_blank_values=True)
        return len(qs) == 1 and qs[0][0] == "v"
    if p.startswith("/@fs/"):
        if query:
            return False
        raw_fs = p[len("/@fs/"):]
        target = os.path.normcase(os.path.realpath(raw_fs))
        if not (target.startswith(ROOT_DIR + os.sep) and any(target.endswith(ext) for ext in STATIC_EXTENSIONS)):
            return False
        return os.path.isfile(target)
    return False

def is_allowed_vite_ws(ws_url: str) -> bool:
    u = urlsplit(ws_url)
    if u.scheme != "ws" or u.netloc != f"127.0.0.1:{PORT}" or u.path not in ("", "/"):
        return False
    qs = parse_qsl(u.query, keep_blank_values=True)
    if len(qs) != 1 or qs[0][0] != "token":
        return False
    owned_token = get_owned_vite_ws_token()
    return bool(owned_token and qs[0][1] == owned_token)

def install_network_guard(page, mock_handler: Optional[Callable] = None, unexpected_list: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    unexpected = unexpected_list if unexpected_list is not None else []

    def handle_request(route):
        req, url, method = route.request, route.request.url, route.request.method
        u = urlsplit(url)
        origin, path = f"{u.scheme}://{u.netloc}", unquote(u.path)
        if origin != ORIGIN:
            unexpected.append({"type": "OUTBOUND", "url": url, "method": method})
            route.abort()
            return
        if path == COPILOT_PATH:
            if method != "POST" or u.query:
                unexpected.append({"type": "METHOD_QUERY", "url": url, "method": method})
                route.abort()
                return
            if mock_handler and mock_handler(route, path):
                return
            unexpected.append({"type": "UNHANDLED_COPILOT", "url": url, "method": method})
            route.abort()
            return
        if path in INVOICE_PATHS:
            if method != "POST" or u.query:
                unexpected.append({"type": "METHOD_QUERY", "url": url, "method": method})
                route.abort()
                return
            if mock_handler and mock_handler(route, path):
                return
            unexpected.append({"type": "UNHANDLED_INVOICE", "url": url, "method": method})
            route.abort()
            return
        if path == SESSION_PATH:
            if method != "GET" or u.query:
                unexpected.append({"type": "METHOD_QUERY", "url": url, "method": method})
                route.abort()
                return
            if mock_handler and mock_handler(route, path):
                return
            route.fulfill(status=200, content_type="application/json", body='{"user":"Administrator","csrf_token":"csrf-test-token-valid"}')
            return
        if path == COMPANY_PATH:
            if method != "GET" or u.query:
                unexpected.append({"type": "METHOD_QUERY", "url": url, "method": method})
                route.abort()
                return
            if mock_handler and mock_handler(route, path):
                return
            route.fulfill(status=200, content_type="application/json", body='{"data":[{"name":"Company A"},{"name":"Company B"}]}')
            return
        if path.startswith("/api/"):
            unexpected.append({"type": "UNDECLARED_API", "url": url, "method": method})
            route.abort()
            return
        if is_allowed_static_asset(method, u.path, u.query):
            route.continue_()
            return
        unexpected.append({"type": "UNDECLARED_ASSET", "url": url, "method": method})
        route.abort()

    def handle_ws(ws):
        if not is_allowed_vite_ws(ws.url):
            unexpected.append({"type": "WS", "url": ws.url})

    page.route("**/*", handle_request)
    page.route_web_socket("**/*", handle_ws)
    return unexpected

class LifecycleGuard:
    __test__ = False
    def __init__(self, browser, mock_handler: Optional[Callable] = None):
        self.browser = browser
        self.mock_handler = mock_handler
        self.unexpected: List[Dict[str, Any]] = []
        self.page = None

    def __enter__(self):
        self.page = self.browser.new_page(service_workers="block")
        install_network_guard(self.page, lambda route, path: self.mock_handler(route, path) if self.mock_handler else False, self.unexpected)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.page:
            try:
                self.page.close()
            except Exception:
                pass
        assert len(self.unexpected) == 0, f"Unexpected network traffic detected: {self.unexpected}"
        return False
