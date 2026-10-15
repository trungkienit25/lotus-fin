# -*- coding: utf-8 -*-
"""
Frappe Database Session Repository.
Persists Chat Sessions and Messages directly into MariaDB DocTypes:
- tabLotus Chat Session (Parent / Thread)
- tabLotus Chat Message (Child / Message & Step)

Includes automatic Self-Healing DDL to ensure zero-crash resilience even if
bench migrate has not run yet.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from lotus_fin.domain.model.chat_message import ChatMessage
from lotus_fin.domain.model.chat_session import ChatSession
from lotus_fin.domain.model.message_role import MessageRole
from lotus_fin.domain.repository.i_session_repository import ISessionRepository
from lotus_fin.domain.schema.tool_execution_result import ToolExecutionResult

try:
    import frappe
except ImportError:
    frappe = None

_logger = logging.getLogger("lotus_fin.infrastructure.persistence.frappe_database_session_repository")


class FrappeDatabaseSessionRepository(ISessionRepository):
    """
    Database persistence repository utilizing Frappe ORM and direct SQL
    for fast ACID-compliant chat session and message storage.
    """

    def __init__(self):
        self._memory_fallback: Dict[str, ChatSession] = {}
        self._tables_ensured = False

    def _ensure_tables_exist(self) -> None:
        """Self-healing DDL: creates tables if not present in MariaDB."""
        if self._tables_ensured or frappe is None or not hasattr(frappe, "db") or frappe.db is None:
            return

        try:
            # 1. Ensure tabLotus Chat Session
            if not frappe.db.table_exists("Lotus Chat Session"):
                frappe.db.sql("""
                    CREATE TABLE IF NOT EXISTS `tabLotus Chat Session` (
                        `name` VARCHAR(140) NOT NULL PRIMARY KEY,
                        `creation` DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
                        `modified` DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                        `modified_by` VARCHAR(140) DEFAULT 'Administrator',
                        `owner` VARCHAR(140) DEFAULT 'Administrator',
                        `docstatus` INT(1) DEFAULT 0,
                        `idx` INT(8) DEFAULT 0,
                        `session_id` VARCHAR(140) NOT NULL UNIQUE,
                        `title` VARCHAR(255),
                        `company` VARCHAR(140) NOT NULL,
                        `user` VARCHAR(140),
                        `status` VARCHAR(32) DEFAULT 'Active',
                        `first_prompt` TEXT,
                        `total_messages` INT DEFAULT 0,
                        `last_tool_called` VARCHAR(140),
                        `last_message_at` DATETIME(6),
                        INDEX `idx_session_company` (`company`),
                        INDEX `idx_session_user` (`user`),
                        INDEX `idx_session_last_msg` (`last_message_at`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)
                frappe.db.commit()
                _logger.info("Self-healing DDL: Created `tabLotus Chat Session` table.")

            # 2. Ensure tabLotus Chat Message
            if not frappe.db.table_exists("Lotus Chat Message"):
                frappe.db.sql("""
                    CREATE TABLE IF NOT EXISTS `tabLotus Chat Message` (
                        `name` VARCHAR(140) NOT NULL PRIMARY KEY,
                        `creation` DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
                        `modified` DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                        `modified_by` VARCHAR(140) DEFAULT 'Administrator',
                        `owner` VARCHAR(140) DEFAULT 'Administrator',
                        `docstatus` INT(1) DEFAULT 0,
                        `idx` INT(8) DEFAULT 0,
                        `message_id` VARCHAR(140) NOT NULL UNIQUE,
                        `session` VARCHAR(140) NOT NULL,
                        `seq_id` INT DEFAULT 0,
                        `role` VARCHAR(32) NOT NULL,
                        `trace_id` VARCHAR(64),
                        `tool_called` VARCHAR(140),
                        `execution_status` VARCHAR(32) DEFAULT 'SUCCESS',
                        `latency_ms` INT DEFAULT 0,
                        `llm_provider` VARCHAR(64),
                        `model_name` VARCHAR(64),
                        `timestamp` DATETIME(6),
                        `content` LONGTEXT,
                        `tool_inputs` LONGTEXT,
                        `tool_output` LONGTEXT,
                        `ui_widget` LONGTEXT,
                        INDEX `idx_msg_session` (`session`),
                        INDEX `idx_msg_trace` (`trace_id`),
                        INDEX `idx_msg_time` (`timestamp`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)
                frappe.db.commit()
                _logger.info("Self-healing DDL: Created `tabLotus Chat Message` table.")

            self._tables_ensured = True
        except Exception as e:
            _logger.warning("Error checking or creating chat tables: %s", e)

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        if frappe is None or not hasattr(frappe, "db") or frappe.db is None:
            return self._memory_fallback.get(session_id)

        self._ensure_tables_exist()

        try:
            # Query session header
            session_rows = frappe.db.sql(
                """
                SELECT session_id, company, user, title, creation, modified
                FROM `tabLotus Chat Session`
                WHERE session_id = %s LIMIT 1
                """,
                (session_id,),
                as_dict=True
            )
            if not session_rows:
                return self._memory_fallback.get(session_id)

            s_data = session_rows[0]

            # Query messages ordered by seq_id or creation
            msg_rows = frappe.db.sql(
                """
                SELECT message_id, role, content, tool_called, tool_inputs, tool_output, ui_widget, timestamp
                FROM `tabLotus Chat Message`
                WHERE session = %s
                ORDER BY seq_id ASC, creation ASC
                """,
                (session_id,),
                as_dict=True
            )

            messages: List[ChatMessage] = []
            tool_traces: List[ToolExecutionResult] = []

            for m in msg_rows:
                try:
                    r_enum = MessageRole(m.get("role", "user").lower())
                except ValueError:
                    r_enum = MessageRole.USER

                messages.append(ChatMessage(
                    role=r_enum,
                    content=m.get("content") or ""
                ))

                # Reconstruct tool trace if present
                if m.get("tool_called") and m.get("tool_output"):
                    try:
                        out_dict = json.loads(m["tool_output"]) if isinstance(m["tool_output"], str) else m["tool_output"]
                        widget_dict = json.loads(m["ui_widget"]) if m.get("ui_widget") and isinstance(m["ui_widget"], str) else m.get("ui_widget")
                        tool_traces.append(ToolExecutionResult(
                            tool_name=m["tool_called"],
                            status="SUCCESS",
                            data=out_dict,
                            ui_widget=widget_dict
                        ))
                    except Exception:
                        pass

            created_at = s_data.get("creation") or datetime.now(timezone.utc)
            updated_at = s_data.get("modified") or datetime.now(timezone.utc)

            return ChatSession(
                id=session_id,
                user_id=s_data.get("user") or "Administrator",
                company=s_data.get("company") or "Lotus-fin (Demo)",
                messages=messages,
                tool_traces=tool_traces,
                created_at=created_at if isinstance(created_at, datetime) else datetime.now(timezone.utc),
                updated_at=updated_at if isinstance(updated_at, datetime) else datetime.now(timezone.utc)
            )
        except Exception as e:
            _logger.warning("Database retrieval error for session %s: %s, falling back to memory", session_id, e)
            return self._memory_fallback.get(session_id)

    def save_session(self, session: ChatSession) -> None:
        # Update memory fallback
        self._memory_fallback[session.id] = session

        if frappe is None or not hasattr(frappe, "db") or frappe.db is None:
            return

        self._ensure_tables_exist()

        try:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            title = session.id
            first_prompt = ""
            for msg in session.messages:
                if msg.role == MessageRole.USER and msg.content:
                    first_prompt = msg.content[:250]
                    title = msg.content[:60] + ("..." if len(msg.content) > 60 else "")
                    break

            last_tool = session.tool_traces[-1].tool_name if session.tool_traces else None

            # Upsert Session row
            existing = frappe.db.sql(
                "SELECT name FROM `tabLotus Chat Session` WHERE session_id = %s",
                (session.id,)
            )

            if existing:
                frappe.db.sql(
                    """
                    UPDATE `tabLotus Chat Session`
                    SET modified = %s, total_messages = %s, last_tool_called = %s, last_message_at = %s, title = COALESCE(NULLIF(title, ''), %s)
                    WHERE session_id = %s
                    """,
                    (now_str, len(session.messages), last_tool, now_str, title, session.id)
                )
            else:
                frappe.db.sql(
                    """
                    INSERT INTO `tabLotus Chat Session`
                    (name, session_id, company, user, title, first_prompt, status, total_messages, last_tool_called, last_message_at, creation, modified)
                    VALUES (%s, %s, %s, %s, %s, %s, 'Active', %s, %s, %s, %s, %s)
                    """,
                    (session.id, session.id, session.company, session.user_id, title, first_prompt, len(session.messages), last_tool, now_str, now_str, now_str)
                )

            # Insert new messages
            existing_count = frappe.db.sql(
                "SELECT COUNT(*) FROM `tabLotus Chat Message` WHERE session = %s",
                (session.id,)
            )[0][0]

            if len(session.messages) > existing_count:
                for idx, msg in enumerate(session.messages[existing_count:], start=existing_count + 1):
                    msg_id = f"msg_{uuid.uuid4().hex[:12]}"
                    tool_name = None
                    tool_inputs = None
                    tool_output = None
                    ui_widget = None

                    # If assistant message correlated with a tool execution
                    if msg.role == MessageRole.ASSISTANT and session.tool_traces:
                        latest_trace = session.tool_traces[-1]
                        tool_name = latest_trace.tool_name
                        tool_output = json.dumps(latest_trace.data, ensure_ascii=False) if latest_trace.data else None
                        ui_widget = json.dumps(latest_trace.ui_widget, ensure_ascii=False) if latest_trace.ui_widget else None

                    frappe.db.sql(
                        """
                        INSERT INTO `tabLotus Chat Message`
                        (name, message_id, session, seq_id, role, content, tool_called, tool_output, ui_widget, timestamp, creation, modified)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (msg_id, msg_id, session.id, idx, msg.role.value, msg.content or "", tool_name, tool_output, ui_widget, now_str, now_str, now_str)
                    )

            frappe.db.commit()
        except Exception as e:
            _logger.error("Failed to save session %s to database: %s", session.id, e)
            try:
                frappe.db.rollback()
            except Exception:
                pass

    def clear_session(self, session_id: str) -> None:
        self._memory_fallback.pop(session_id, None)

        if frappe is None or not hasattr(frappe, "db") or frappe.db is None:
            return

        try:
            frappe.db.sql("DELETE FROM `tabLotus Chat Message` WHERE session = %s", (session_id,))
            frappe.db.sql("DELETE FROM `tabLotus Chat Session` WHERE session_id = %s", (session_id,))
            frappe.db.commit()
        except Exception as e:
            _logger.warning("Failed to clear session %s from database: %s", session_id, e)

    def list_sessions(self, company: Optional[str] = None, user_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        if frappe is None or not hasattr(frappe, "db") or frappe.db is None:
            res = []
            for s in list(self._memory_fallback.values())[:limit]:
                res.append({
                    "id": s.id,
                    "session_id": s.id,
                    "company": s.company,
                    "title": s.messages[0].content[:60] if s.messages else s.id,
                    "last_message_at": str(s.updated_at),
                    "total_messages": len(s.messages)
                })
            return res

        self._ensure_tables_exist()

        try:
            conditions = ["1=1"]
            params = []
            if company:
                conditions.append("company = %s")
                params.append(company)
            if user_id:
                conditions.append("user = %s")
                params.append(user_id)

            params.append(limit)
            query = f"""
                SELECT session_id as id, session_id, title, company, user, total_messages, last_tool_called, last_message_at, creation
                FROM `tabLotus Chat Session`
                WHERE {' AND '.join(conditions)}
                ORDER BY last_message_at DESC, modified DESC
                LIMIT %s
            """
            rows = frappe.db.sql(query, tuple(params), as_dict=True)
            return [dict(r) for r in rows]
        except Exception as e:
            _logger.warning("Failed to list sessions from database: %s", e)
            return []
