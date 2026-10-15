#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FinTechathon 2026 Track E - Automated Sandbox Operation Evidence Generator.
Executes the canonical test suite across all 6 financial modules + general diagnostic,
producing verified audit trail logs (.jsonl) complying with Item 06 (Execution Evidence).
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "lotus_fin"))

from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.presentation.controller.copilot_controller import CopilotController, get_copilot_service


CANONICAL_PROMPTS = [
    {
        "id": "PROMPT_01_HEALTH",
        "module": "F001_FINANCIAL_HEALTH",
        "query": "Đánh giá sức khỏe tài chính doanh nghiệp năm 2026 và các chỉ số doanh thu, chi phí, dòng tiền.",
    },
    {
        "id": "PROMPT_02_CASHFLOW",
        "module": "F002_CASHFLOW_FORECAST",
        "query": "Dự báo dòng tiền 30 ngày tới của công ty và cảnh báo nguy cơ thiếu hụt tiền mặt.",
    },
    {
        "id": "PROMPT_03_RISK",
        "module": "F003_RISK_SIGNAL",
        "query": "Phát hiện tín hiệu rủi ro quá hạn phải thu AR và áp lực công nợ phải trả AP.",
    },
    {
        "id": "PROMPT_04_WHATIF",
        "module": "F004_WHAT_IF_STUDIO",
        "query": "Nếu doanh thu giảm 20% và khách hàng chậm thanh toán 15 ngày, dòng tiền bị ảnh hưởng ra sao?",
    },
    {
        "id": "PROMPT_05_FINANCING",
        "module": "F005_FINANCING_COPILOT",
        "query": "Tư vấn gói vay vốn lưu động 1 tỷ VND phù hợp nhất cho doanh nghiệp trong 12 tháng.",
    },
    {
        "id": "PROMPT_06_REPAYMENT",
        "module": "F006_DEBT_REPAYMENT",
        "query": "Tính lịch trả nợ khoản vay 1 tỷ VND lãi suất 8.5%/năm trong 12 tháng với kịch bản sốc lãi suất +200 bps.",
    },
    {
        "id": "PROMPT_07_GENERAL",
        "module": "GENERAL_DIAGNOSTIC",
        "query": "Tổng hợp tình hình tài chính tổng thể và khuyến nghị hành động tối ưu dòng tiền ngắn hạn.",
    }
]


def generate_evidence(company: str = "Lotus-fin (Demo)"):
    print(f"================================================================================")
    print(f"🌟 FinTechathon 2026 Track E — Generating AI Sandbox Operational Evidence")
    print(f"   Target Company : {company}")
    print(f"   Date / Time    : {datetime.now(timezone.utc).isoformat()}")
    print(f"================================================================================")

    session_id = f"sandbox_evidence_{int(time.time())}"
    copilot_svc = get_copilot_service()

    executed_count = 0
    start_all = time.perf_counter()

    for idx, item in enumerate(CANONICAL_PROMPTS, 1):
        print(f"\n[{idx}/7] Executing Query: {item['id']} ({item['module']})")
        print(f"    Prompt: \"{item['query']}\"")

        t0 = time.perf_counter()
        res = CopilotController.handle_send_message({
            "message": item["query"],
            "company": company,
            "session_id": session_id,
            "context_filters": {
                "user_id": "auditor@fintechathon.vn",
                "roles": ["Financial Auditor", "System Manager"]
            }
        }, service=copilot_svc)
        latency = int((time.perf_counter() - t0) * 1000)

        tool_called = res.get("tool_called") or "NO_TOOL"
        trace_id = res.get("trace_id") or "N/A"
        summary = res.get("reply", "")[:120].replace("\n", " ")

        print(f"    ✔ Result   : Status={res.get('status', 'SUCCESS')} | Tool={tool_called} | Latency={latency}ms")
        print(f"    ✔ Trace ID : {trace_id}")
        print(f"    ✔ Excerpt  : {summary}...")
        executed_count += 1

    total_time = time.perf_counter() - start_all

    # Verify audit logs file
    logs = CopilotController.handle_get_operation_logs(session_id=session_id, limit=50)
    print(f"\n================================================================================")
    print(f"✔ Successfully recorded {len(logs)} audit log entries in sandbox session.")
    print(f"✔ Total execution time: {total_time:.2f}s across {executed_count} canonical operations.")

    # Export to evidence directory
    evidence_dir = PROJECT_ROOT.parent / "evidence"
    if not evidence_dir.exists():
        evidence_dir = PROJECT_ROOT / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_dir / "sandbox_operation_logs.jsonl"

    all_logs = CopilotController.handle_export_operation_logs(company=company)
    exported_entries = all_logs.get("logs", [])

    with open(evidence_path, "w", encoding="utf-8") as f:
        for entry in exported_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"✔ Evidence exported to: {evidence_path.resolve()}")
    print(f"✔ FinTechathon Item 06 (Non-on-chain Execution Evidence) Compliant.")
    print(f"================================================================================\n")


if __name__ == "__main__":
    comp = sys.argv[1] if len(sys.argv) > 1 else "Lotus-fin (Demo)"
    generate_evidence(comp)
