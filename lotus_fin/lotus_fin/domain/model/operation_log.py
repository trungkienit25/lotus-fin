# -*- coding: utf-8 -*-
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def local_now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class SandboxOperationLogEntry(BaseModel):
    """
    Domain Entity representing an automated audit trace of AI operations in sandbox.
    Compliant with FinTechathon 2026 Item 06 (Execution Evidence) and
    OpenTelemetry GenAI Semantic Conventions.
    """
    log_id: str = Field(..., description="Unique trace identifier (UUID4)")
    timestamp_utc: str = Field(default_factory=utc_now_iso, description="ISO-8601 UTC timestamp")
    timestamp_local: str = Field(default_factory=local_now_str, description="Local formatted timestamp")
    environment: str = Field(default="SANDBOX", description="Execution environment: SANDBOX | PRODUCTION")
    user_principal: str = Field(..., description="User ID or principal executing the query")
    user_roles: List[str] = Field(default_factory=list, description="Roles attached to user principal")
    company: str = Field(..., description="Target company boundary (e.g. Lotus-fin Demo)")
    session_id: str = Field(..., description="Chat session identifier")
    prompt_query: str = Field(..., description="Natural language prompt query submitted")
    agent_intent: Optional[str] = Field(default=None, description="Inferred domain intent (e.g. F001..F006)")
    tool_called: Optional[str] = Field(default=None, description="Deterministic financial tool dispatched")
    tool_inputs: Optional[Dict[str, Any]] = Field(default=None, description="Input parameters passed to the tool")
    accounting_ledger_accessed: List[str] = Field(default_factory=list, description="Ledgers and DocTypes queried")
    execution_status: str = Field(default="SUCCESS", description="SUCCESS | FAILED | REJECTED")
    latency_ms: int = Field(default=0, description="End-to-end execution latency in milliseconds")
    llm_provider: str = Field(default="unknown", description="Underlying LLM provider adapter")
    model_name: Optional[str] = Field(default=None, description="Underlying model name")
    summary_output: str = Field(..., description="Sanitized natural language or widget summary returned")

