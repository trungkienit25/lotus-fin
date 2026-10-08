"""
Lotus Fin AI001 - Grounded LLM Explanation Provider & Engine.
Provides multi-provider explanation synthesis, schema validation, and telemetry.
"""

from decimal import Decimal
import json
import logging
import os
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from lotus_fin.ai.observability import log_event
from lotus_fin.modules.f001_health.explanation_validator import (
    SYSTEM_PROMPT,
    extract_numbers_from_text,
    validate_explanation_schema,
    validate_grounding,
    sanitize_text,
    build_minimized_model_payload
)

_logger = logging.getLogger("lotus_fin.ai001.explanation")

EVENT_LLM_REQUEST_STARTED = "ai001_llm_request_started"
EVENT_LLM_REQUEST_COMPLETED = "ai001_llm_request_completed"
EVENT_LLM_REQUEST_FAILED = "ai001_llm_request_failed"
EVENT_LLM_GROUNDING_FAILED = "ai001_llm_grounding_failed"
EVENT_LLM_SCHEMA_INVALID = "ai001_llm_schema_invalid"

PROMPT_VERSION = "2026.09-v1"

MODEL_COST_PER_1K = {
    "mock": {"input": 0.0, "output": 0.0},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "claude-3-5-haiku-20241022": {"input": 0.0008, "output": 0.004},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003}
}



class LLMExplanationProvider:
    """Manages LLM invocations with mock fallback and remote provider support."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider_type: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_seconds: float = 10.0,
        mock_handler: Optional[Callable[[Dict[str, Any]], str]] = None
    ):
        gemini_key = os.environ.get("GEMINI_API_KEY")
        self.api_key = api_key or gemini_key or os.environ.get("LOTUS_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
        
        in_test = False
        try:
            import frappe
            in_test = bool(getattr(frappe.flags, "in_test", False))
        except Exception:
            pass
        if "unittest" in sys.modules:
            in_test = True

        default_provider = "mock" if (in_test or not self.api_key) else (os.environ.get("LOTUS_AI_PROVIDER") or os.environ.get("LOTUS_LLM_PROVIDER") or "gemini")
        self.provider_type = provider_type or default_provider

        if self.provider_type in ["gemini", "google"]:
            cand = model_name or os.environ.get("LOTUS_LLM_MODEL") or "gemini-flash-lite-latest"
            if cand in ["gemini-1.5-flash", "gemini-flash-latest", "gemini-2.5-flash"]:
                cand = "gemini-flash-lite-latest"
            self.model_name = cand
        else:
            self.model_name = model_name or os.environ.get("LOTUS_LLM_MODEL", "gpt-4o-mini")
        self.timeout_seconds = timeout_seconds
        self.mock_handler = mock_handler

    def generate_explanation_raw(self, payload: Dict[str, Any]) -> Tuple[int, str, Dict[str, Any]]:
        if self.mock_handler:
            return 200, self.mock_handler(payload), {"tokens_in": 120, "tokens_out": 85}
        if self.provider_type == "mock":
            return self._generate_default_mock(payload)
        return self._call_remote_provider(payload)

    def _generate_default_mock(self, payload: Dict[str, Any]) -> Tuple[int, str, Dict[str, Any]]:
        metrics_by_id = {m["metric_id"]: m for m in payload.get("metrics", [])}
        facts = []
        for mid, label in [("revenue", "Recorded revenue for the period is"), ("cogs", "Cost of goods sold is"), ("cash_balance", "Closing cash balance is")]:
            m = metrics_by_id.get(mid)
            if m and m.get("status") == "AVAILABLE":
                facts.append(f"{label} {m['value']} {payload.get('currency', 'VND')}.")

        gm = metrics_by_id.get("gross_margin")
        if gm and gm.get("status") == "AVAILABLE":
            pct = round(float(gm['value']) * 100, 2)
            facts.append(f"Gross margin stands at {gm['value']} ({pct}%).")

        ar, ar_ratio = metrics_by_id.get("ar_outstanding"), metrics_by_id.get("overdue_ar_ratio")
        if ar and ar.get("status") == "AVAILABLE":
            txt = f"Accounts receivable outstanding is {ar['value']} {payload.get('currency', 'VND')}."
            if ar_ratio and ar_ratio.get("status") == "AVAILABLE":
                txt += f" Overdue receivables ratio is {ar_ratio['value']}."
            facts.append(txt)

        ap = metrics_by_id.get("ap_outstanding")
        if ap and ap.get("status") == "AVAILABLE":
            facts.append(f"Accounts payable outstanding is {ap['value']} {payload.get('currency', 'VND')}.")

        comp = payload.get("comparison")
        if isinstance(comp, dict) and comp.get("status") == "AVAILABLE" and comp.get("metrics"):
            for comp_k, comp_v in comp["metrics"].items():
                if isinstance(comp_v, dict) and comp_v.get("previous") is not None:
                    facts.append(
                        f"Compared to previous period, {comp_k} changed from {comp_v['previous']} to {comp_v.get('current', '')}."
                    )

        if not facts:
            facts.append("Core financial metrics are unavailable or incomplete for this period.")

        mock_obj = {
            "status": "AVAILABLE",
            "facts": facts,
            "interpretations": ["Revenue and working capital metrics verified from general ledger."],
            "next_checks": [
                "Review aged accounts receivable ledger for invoices exceeding credit terms.",
                "Verify bank reconciliation statements to confirm actual cash and overdraft balances."
            ]
        }
        return 200, json.dumps(mock_obj), {"tokens_in": 150, "tokens_out": 95}

    def _call_remote_provider(self, payload: Dict[str, Any]) -> Tuple[int, str, Dict[str, Any]]:
        import urllib.request, urllib.error
        if self.provider_type in ["gemini", "google"] or "gemini" in self.model_name.lower():
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
            body_data = {
                "contents": [
                    {"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTION: {SYSTEM_PROMPT}"}]},
                    {"role": "model", "parts": [{"text": "Understood. I will provide strictly grounded JSON output."}]},
                    {"role": "user", "parts": [{"text": json.dumps(payload, default=str)}]}
                ],
                "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"}
            }
            req = urllib.request.Request(url, data=json.dumps(body_data).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                    resp_json = json.loads(resp.read().decode("utf-8"))
                    usage = resp_json.get("usageMetadata", {})
                    candidates = resp_json.get("candidates", [{}])
                    content_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
                    return resp.getcode(), content_text, {
                        "tokens_in": usage.get("promptTokenCount", 0), "tokens_out": usage.get("candidatesTokenCount", 0)
                    }
            except urllib.error.HTTPError as e:
                return e.code, e.read().decode("utf-8") if e.fp else str(e), {}
            except urllib.error.URLError as e:
                return 504, json.dumps({"error": f"Timeout error: {str(e)}"}), {}
            except Exception as e:
                return 500, json.dumps({"error": f"Provider error: {str(e)}"}), {}

        endpoint = os.environ.get("LOTUS_LLM_ENDPOINT", "https://api.openai.com/v1/chat/completions")
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        body_data = {
            "model": self.model_name,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": json.dumps(payload, default=str)}],
            "temperature": 0.0, "response_format": {"type": "json_object"}
        }
        req = urllib.request.Request(endpoint, data=json.dumps(body_data).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                resp_json = json.loads(resp.read().decode("utf-8"))
                usage = resp_json.get("usage", {})
                return resp.getcode(), resp_json.get("choices", [{}])[0].get("message", {}).get("content", "{}"), {
                    "tokens_in": usage.get("prompt_tokens", 0), "tokens_out": usage.get("completion_tokens", 0)
                }
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8") if e.fp else str(e), {}
        except urllib.error.URLError as e:
            return 504, json.dumps({"error": f"Timeout error: {str(e)}"}), {}
        except Exception as e:
            return 500, json.dumps({"error": f"Provider error: {str(e)}"}), {}


def generate_financial_explanation(
    snapshot: Dict[str, Any],
    provider: Optional[LLMExplanationProvider] = None,
    correlation_id: Optional[str] = None
) -> Dict[str, Any]:
    cid = correlation_id or snapshot.get("correlation_id", "CID-UNKNOWN")
    prov = provider or LLMExplanationProvider()

    if snapshot.get("status") in ["FORBIDDEN", "VALIDATION_ERROR"]:
        return {"status": "UNAVAILABLE", "facts": [], "interpretations": [], "next_checks": []}

    available_metrics = [m for m in snapshot.get("metrics", []) if m.get("status") == "AVAILABLE"]
    if not available_metrics:
        return {
            "status": "UNAVAILABLE",
            "facts": ["Financial metrics unavailable from source ledgers."],
            "interpretations": ["Insufficient data to perform automated financial health assessment."],
            "next_checks": ["Investigate ERPNext report source connectivity and data entry status."]
        }

    try:
        http_code, response_raw, usage = prov.generate_explanation_raw(build_minimized_model_payload(snapshot))
    except Exception as e:
        return {"status": "UNAVAILABLE", "facts": [], "interpretations": [], "next_checks": ["Model explanation unavailable due to provider invocation failure."]}

    if http_code != 200:
        return {"status": "UNAVAILABLE", "facts": [], "interpretations": [], "next_checks": [f"Model service returned status {http_code}; explanation unavailable."]}

    try:
        parsed_json = json.loads(response_raw)
    except Exception:
        return {"status": "UNAVAILABLE", "facts": [], "interpretations": [], "next_checks": ["Model produced invalid non-JSON output; explanation unavailable."]}

    is_valid_schema, clean_exp, _ = validate_explanation_schema(parsed_json)
    if not is_valid_schema:
        return {"status": "UNAVAILABLE", "facts": [], "interpretations": [], "next_checks": ["Model response failed strict schema validation."]}

    is_grounded, errors = validate_grounding(clean_exp, snapshot)
    if not is_grounded:
        return {"status": "UNAVAILABLE", "facts": [], "interpretations": [], "next_checks": ["Automated explanation was rejected by grounding verification due to unverified numeric claims."]}

    return clean_exp
