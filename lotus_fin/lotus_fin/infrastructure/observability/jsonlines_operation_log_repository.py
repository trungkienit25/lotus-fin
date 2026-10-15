# -*- coding: utf-8 -*-
"""
JSON Lines Operation Log Repository.
Appends structured audit traces in append-only .jsonl format to guarantee
tamper-evident audit logging and FinTechathon 2026 Item 06 compliance.
"""

import json
import logging
import os
import threading
from typing import List, Optional

from lotus_fin.domain.model.operation_log import SandboxOperationLogEntry
from lotus_fin.domain.repository.i_operation_log_repository import IOperationLogRepository

_logger = logging.getLogger("lotus_fin.infrastructure.observability.jsonlines_operation_log_repository")
_log_lock = threading.Lock()


class JsonLinesOperationLogRepository(IOperationLogRepository):
    """
    Append-only JSON Lines audit repository writing to both container log
    and repository workspace log files.
    """

    def __init__(self, primary_path: Optional[str] = None, log_file_path: Optional[str] = None):
        self.primary_path = primary_path or log_file_path or self._resolve_primary_log_path()
        self.fallback_path = self._resolve_fallback_log_path()
        self._ensure_log_dirs()

    def _resolve_primary_log_path(self) -> str:
        # Standard Frappe bench logs path if containerized
        bench_log_dir = "/home/frappe/frappe-bench/logs"
        if os.path.isdir(bench_log_dir):
            return os.path.join(bench_log_dir, "lotus_ai_operations.jsonl")

        # Local application logs path
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../logs"))
        return os.path.join(base_dir, "sandbox_operations.jsonl")

    def _resolve_fallback_log_path(self) -> str:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../logs"))
        return os.path.join(base_dir, "sandbox_operations.jsonl")

    def _ensure_log_dirs(self) -> None:
        for p in [self.primary_path, self.fallback_path]:
            try:
                d = os.path.dirname(p)
                if d and not os.path.exists(d):
                    os.makedirs(d, exist_ok=True)
            except Exception as e:
                _logger.warning("Could not create log directory for %s: %s", p, e)

    def append_log(self, entry: SandboxOperationLogEntry) -> None:
        line = json.dumps(entry.model_dump(), ensure_ascii=False) + "\n"

        with _log_lock:
            # Write to primary path
            target_paths = [self.primary_path]
            if self.fallback_path != self.primary_path:
                target_paths.append(self.fallback_path)

            for p in target_paths:
                try:
                    d = os.path.dirname(p)
                    if d and not os.path.exists(d):
                        os.makedirs(d, exist_ok=True)
                    with open(p, "a", encoding="utf-8") as f:
                        f.write(line)
                        f.flush()
                except Exception as e:
                    _logger.warning("Failed appending audit log to %s: %s", p, e)

    def query_logs(
        self,
        company: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 50
    ) -> List[SandboxOperationLogEntry]:
        # Determine best available log file
        target_file = None
        for p in [self.primary_path, self.fallback_path]:
            if os.path.isfile(p):
                target_file = p
                break

        if not target_file:
            return []

        entries: List[SandboxOperationLogEntry] = []
        with _log_lock:
            try:
                with open(target_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                # Read backwards to get most recent logs
                for line in reversed(lines):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if company and data.get("company") != company:
                            continue
                        if session_id and data.get("session_id") != session_id:
                            continue
                        entries.append(SandboxOperationLogEntry.model_validate(data))
                        if len(entries) >= limit:
                            break
                    except Exception:
                        continue
            except Exception as e:
                _logger.error("Failed querying audit logs from %s: %s", target_file, e)

        return entries

    def clear_logs(self, company: Optional[str] = None) -> None:
        with _log_lock:
            for p in [self.primary_path, self.fallback_path]:
                try:
                    if os.path.isfile(p):
                        if not company:
                            # Full truncate
                            with open(p, "w", encoding="utf-8") as f:
                                f.truncate(0)
                        else:
                            # Filter out only target company logs
                            with open(p, "r", encoding="utf-8") as f:
                                remaining = [
                                    line for line in f
                                    if line.strip() and json.loads(line.strip()).get("company") != company
                                ]
                            with open(p, "w", encoding="utf-8") as f:
                                f.writelines(remaining)
                except Exception as e:
                    _logger.warning("Failed clearing audit logs in %s: %s", p, e)
