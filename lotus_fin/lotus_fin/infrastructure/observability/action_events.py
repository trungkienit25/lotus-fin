"""Required action audit delivery with acknowledged stream writes.

SSOT §6; ADR001. No durability guarantee or generic logging fallback.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from lotus_fin.application.port.i_action_events import (
    ActionEvent,
    ActionEventDeliveryError,
    IActionEventsPort,
)

logger = logging.getLogger("lotus_fin.actions.observability")


class SafeStructuredActionEvents(IActionEventsPort):
    """Required sink contract: ordinary Logger/StreamHandler policy, full write + flush.

    All non-Null handlers are required. Suppression or unsupported delivery
    fails closed. Only inherited standard handle/emit semantics are supported;
    generic, buffering, queued and custom emit/handle sinks require another port.
    Stream.write must return the full character count; flush must return normally.
    Delivery acknowledges the stream interface, not persistence or durability.
    """

    def __init__(self, target_logger: Optional[logging.Logger] = None) -> None:
        self._logger = target_logger if target_logger is not None else logger
        self._recorded_events: List[Dict[str, Any]] = []

    @property
    def recorded_events(self) -> List[Dict[str, Any]]:
        """Events acknowledged by every required sink."""
        return self._recorded_events

    def _get_effective_handlers(self) -> List[logging.Handler]:
        handlers: List[logging.Handler] = []
        cur = self._logger
        seen = set()
        while cur:
            for h in cur.handlers:
                if id(h) not in seen:
                    seen.add(id(h))
                    handlers.append(h)
            if not cur.propagate:
                break
            cur = cur.parent
        return handlers

    def record_event(self, event: ActionEvent) -> None:
        clean_dict = event.model_dump(mode="json")
        try:
            log = self._logger
            if type(log) is not logging.Logger or not log.isEnabledFor(logging.INFO):
                raise ValueError("Unsupported or suppressed logger")
            # Customized logger delivery could suppress a record; do not bypass it.
            for name in ("info", "_log", "handle", "callHandlers"):
                if getattr(getattr(log, name), "__func__", None) is not getattr(logging.Logger, name):
                    raise ValueError("Unsupported logger delivery")
            record = log.makeRecord(log.name, logging.INFO, "", 0,
                                    json.dumps(clean_dict, default=str), (), None)
            filtered = log.filter(record)
            if not filtered:
                raise ValueError("Logger rejected required event")
            if isinstance(filtered, logging.LogRecord):
                record = filtered
            active = [h for h in self._get_effective_handlers()
                      if not isinstance(h, logging.NullHandler)]
            if not active or any(h.level > logging.INFO for h in active):
                raise ValueError("Missing or suppressed required sink")
            prepared = []
            # Check all policies before writing to any sink. Ancestor logger filters
            # are not applied, matching ordinary logging propagation semantics.
            for h in active:
                h.acquire()
                try:
                    filtered = h.filter(record)
                    if not filtered:
                        raise ValueError("Handler rejected required event")
                    if (not isinstance(h, logging.StreamHandler)
                            or getattr(h.emit, "__func__", None) is not logging.StreamHandler.emit
                            or getattr(h.handle, "__func__", None) is not logging.Handler.handle):
                        raise ValueError("Unsupported sink acknowledgment")
                    prepared.append((h, filtered if isinstance(filtered, logging.LogRecord) else record))
                finally:
                    h.release()
            for h, sink_record in prepared:
                h.acquire()
                try:
                    message = h.format(sink_record) + h.terminator
                    written = h.stream.write(message)
                    if type(written) is not int or written != len(message):
                        raise ValueError("Incomplete sink acknowledgment")
                    h.flush()
                finally:
                    h.release()
        except Exception:
            raise ActionEventDeliveryError("Required action audit delivery failed.") from None
        self._recorded_events.append(clean_dict)
