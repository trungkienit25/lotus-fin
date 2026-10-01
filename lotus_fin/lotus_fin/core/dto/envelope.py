from datetime import datetime, timezone
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field
import uuid

T = TypeVar("T")


class ResponseMeta(BaseModel):
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    version: str = "1.0.0"
    duration_ms: Optional[float] = None


class ResponseError(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class ApiResponse(BaseModel, Generic[T]):
    """Standardized API envelope conforming to enterprise REST standards."""
    success: bool
    data: Optional[T] = None
    error: Optional[ResponseError] = None
    meta: ResponseMeta = Field(default_factory=ResponseMeta)

    @classmethod
    def ok(cls, data: T, duration_ms: Optional[float] = None) -> "ApiResponse[T]":
        meta = ResponseMeta(duration_ms=duration_ms)
        return cls(success=True, data=data, meta=meta)

    @classmethod
    def fail(cls, code: str, message: str, details: Optional[Any] = None) -> "ApiResponse[Any]":
        meta = ResponseMeta()
        err = ResponseError(code=code, message=message, details=details)
        return cls(success=False, error=err, meta=meta)

    def to_dict(self) -> dict:
        return self.model_dump(exclude_none=True)
