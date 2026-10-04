"""
Lotus Fin AI007 — Models for Financial Copilot Orchestrator.
Defines Intents, Context, Request, and Response structures.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class IntentType(str, Enum):
    """Phân loại ý định của người dùng."""
    FINANCING_SUPPORT = "FINANCING_SUPPORT"        # Cần tìm khoản vay (Gọi AI005)
    REPAYMENT_STRESS = "REPAYMENT_STRESS"          # Mô phỏng trả nợ / Stress test (Gọi AI006)
    HEALTH_CHECK = "HEALTH_CHECK"                  # Phân tích sức khỏe tài chính (AI002/AI004)
    GENERAL_QA = "GENERAL_QA"                      # Hỏi đáp chung về tài chính
    UNKNOWN = "UNKNOWN"                            # Không xác định


@dataclass
class ConversationContext:
    """Ngữ cảnh hội thoại để Copilot ghi nhớ trạng thái."""
    session_id: str
    current_intent: Optional[IntentType] = None
    extracted_entities: Dict[str, Any] = field(default_factory=dict)
    last_action: str = ""
    is_authenticated: bool = True
    company_id: str = ""


@dataclass
class CopilotRequest:
    """Yêu cầu đầu vào từ người dùng gửi tới Copilot."""
    message: str
    session_id: str
    company_id: str = "Lotus_SME"
    context: Optional[Dict[str, Any]] = field(default_factory=dict)


@dataclass
class CopilotAction:
    """Hành động mà Copilot thực thi dưới nền."""
    module_called: str           # Ví dụ: "AI005", "AI006"
    action_type: str             # Ví dụ: "run_stress_test", "match_financing"
    parameters: Dict[str, Any]   # Tham số truyền vào module
    result_summary: str          # Tóm tắt kết quả (nếu có)


@dataclass
class CopilotResponse:
    """Phản hồi cuối cùng của Copilot trả về cho Frontend."""
    session_id: str
    intent: IntentType
    reply_message: str                           # Câu trả lời ngôn ngữ tự nhiên
    actions_taken: List[CopilotAction] = field(default_factory=list)
    suggested_next_steps: List[str] = field(default_factory=list)
    ui_widgets: List[Dict[str, Any]] = field(default_factory=list)  # Data để render biểu đồ/bảng trên UI
    data_mode: str = "simulation"
