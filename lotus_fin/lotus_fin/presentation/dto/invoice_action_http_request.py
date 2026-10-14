"""Strict JSON admission for the existing three invoice action declarations."""

import json
from typing import Any
from lotus_fin.presentation.dto.invoice_action_request import (
    ContextRequestDTO, SearchRequestDTO, OpenRequestDTO,
)

MAX_REQUEST_BYTES = 16 * 1024
REQUEST_MODELS = {"invoice.context": ContextRequestDTO, "invoice.search": SearchRequestDTO,
                  "invoice.open": OpenRequestDTO}


class RequestTooLarge(ValueError):
    """Safe admission failure; no request content is retained."""


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(_value):
    raise ValueError("Non-finite JSON constant")


def parse_invoice_http_request(request: Any, capability: str) -> dict:
    """Validate raw JSON once; framework authentication/CSRF remain upstream."""
    if not request.is_json or request.query_string:
        raise ValueError("JSON body required without query arguments")
    if request.content_length is not None and request.content_length > MAX_REQUEST_BYTES:
        raise RequestTooLarge("Request limit exceeded")
    raw = request.get_data(cache=True)
    if len(raw) > MAX_REQUEST_BYTES:
        raise RequestTooLarge("Request limit exceeded")
    body = json.loads(raw, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    if not isinstance(body, dict):
        raise ValueError("JSON object required")
    dto = REQUEST_MODELS[capability].model_validate(body)
    return dto.model_dump(exclude_unset=True)
