"""Real cookie/session HTTP probes with only synthetic QA identity on owned site."""
import argparse
import http.cookiejar
import json
import pathlib
import urllib.error
import urllib.parse
import urllib.request


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', required=True)
    parser.add_argument('--credentials', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.base != 'http://127.0.0.1:8097':
        parser.error('Qualification is bound to approved loopback target 8097')
    credentials = json.loads(pathlib.Path(args.credentials).read_text(encoding='utf-8'))
    jar = http.cookiejar.CookieJar()
    client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    rows = []
    def probe(name, path, method='GET', data=None, headers=None, statuses=(200,)):
        payload = json.dumps(data).encode() if data is not None else None
        request = urllib.request.Request(args.base + path, data=payload, method=method,
            headers={'Content-Type': 'application/json', **(headers or {})})
        try:
            response = client.open(request, timeout=15)
        except urllib.error.HTTPError as error:
            response = error
        body = response.read()
        status = response.status
        assert status in statuses, f'{name}: unexpected HTTP {status}'
        rows.append({'case': name, 'http_status': status, 'pass': True})
        return body, response.headers
    probe('framework_ping', '/api/method/ping')
    probe('guest_core_denied', '/api/method/lotus_fin.runtime.health.readiness', statuses=(401,403))
    legacy = '/api/method/lotus_fin.api.ai_insights.get_financial_snapshot'
    probe('guest_legacy_denied', legacy, statuses=(401,403))
    probe('guest_legacy_v2_denied', '/api/v2/method/lotus_fin.api.ai_insights.get_risk_signal', statuses=(401,403))
    probe('ordinary_login', '/api/method/login', 'POST', credentials)
    body, _ = probe('ordinary_session_identity', '/api/method/frappe.auth.get_logged_user')
    assert json.loads(body)['message'] == credentials['usr']
    body, _ = probe('ordinary_core_readiness', '/api/method/lotus_fin.runtime.health.readiness')
    assert json.loads(body)['message']['apps'] == ['frappe', 'lotus_fin']
    probe('ordinary_legacy_denied', legacy, statuses=(403,))
    probe('ordinary_legacy_v2_denied', '/api/v2/method/lotus_fin.api.ai_insights.get_risk_signal', statuses=(403,))
    probe('legacy_cmd_override_denied', '/', 'POST', {'cmd': 'lotus_fin.api.ai_insights.get_financial_snapshot'}, statuses=(400,403))
    probe('csrf_missing_denied', '/api/method/lotus_fin.api.invoice_actions_api.get_context',
          'POST', {}, statuses=(400,403))
    body, _ = probe('framework_desk_session', '/app')
    import re
    match = re.search(rb'csrf_token\s*=\s*["\']([^"\']+)', body)
    assert match, 'No framework CSRF token in authenticated Desk response'
    body, headers = probe('native_capability_disabled', '/api/method/lotus_fin.api.invoice_actions_api.get_context',
          'POST', {'request_id': 'f938c3b8-0269-47c3-b8a7-92cbd511a574', 'company_candidate': 'Unqualified QA'},
          {'X-Frappe-CSRF-Token': match.group(1).decode()}, statuses=(503,))
    assert b'CAPABILITY_DISABLED' in body
    assert 'no-store' in headers.get('Cache-Control', '')
    assert b'Traceback' not in body and b'/home/frappe' not in body
    probe('framework_logout', '/api/method/logout', 'POST', {},
          {'X-Frappe-CSRF-Token': match.group(1).decode()})
    probe('expired_session_denied', '/api/method/lotus_fin.runtime.health.readiness', statuses=(401,403))
    pathlib.Path(args.output).write_text(json.dumps({'results': rows,
        'scope': 'Framework auth/session/CSRF and disabled capabilities, no native financial data'}, indent=2), encoding='utf-8')
    print(json.dumps(rows))


if __name__ == '__main__':
    main()
