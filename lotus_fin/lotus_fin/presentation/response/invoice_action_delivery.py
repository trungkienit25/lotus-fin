"""One P1 terminal boundary: safe outcome, sanitized IDs, one required audit."""

from typing import Optional
from lotus_fin.application.port.i_action_events import ActionEvent, ActionEventStage, IActionEventsPort
from lotus_fin.domain.schema.action_outcome import (
    ActionOutcome, ActionStatus as S, ActionReasonCode as R, scan_for_nested_denial,
)
from lotus_fin.presentation.response.action_response import ActionResponseBuilder as B


class InvoiceActionDelivery:
    def __init__(self, events: Optional[IActionEventsPort]):
        self._events = events

    @property
    def available(self) -> bool:
        return self._events is not None

    @staticmethod
    def server_cid(value=None) -> str:
        return B.sanitize_request_id(value)[0]

    def failure(self, status, reason, capability, request_id, cid):
        clean_id, replaced = B.sanitize_request_id(request_id)
        if replaced and status == S.NOT_AVAILABLE:
            reason = R.INVALID_REQUEST
        outcome = B.build_failure_outcome(status, reason, capability,
            client_request_id=clean_id, correlation_id=cid)
        return self.complete(outcome)

    def complete(self, outcome: ActionOutcome):
        # No required sink means no admission: null disabled response, no false audit.
        if not self.available:
            outcome = B.build_failure_outcome(S.NOT_AVAILABLE, R.CAPABILITY_DISABLED,
                outcome.capability, client_request_id=outcome.request_id,
                correlation_id=outcome.correlation_id)
        try:
            if outcome.status in (S.OK, S.PARTIAL) and scan_for_nested_denial(outcome.data):
                outcome = B.build_failure_outcome(S.FORBIDDEN, R.ACCESS_DENIED,
                    outcome.capability, client_request_id=outcome.request_id,
                    correlation_id=outcome.correlation_id)
            response = B.serialize_response(outcome)
        except (ValueError, TypeError):
            # Invalid/mutated success cannot expose data or raw validator errors.
            failure = B.build_failure_outcome(S.SOURCE_ERROR, R.INVALID_PROVIDER_RESPONSE,
                outcome.capability, client_request_id=outcome.request_id,
                correlation_id=outcome.correlation_id)
            response = B.serialize_response(failure)
        if self.available:
            body = response[2]
            event = ActionEvent(correlation_id=body["correlation_id"], request_id=body["request_id"],
                capability=body["capability"], stage=ActionEventStage.RESPONSE_DELIVERY,
                status=S(body["status"]), reason_code=R(body["reason_code"]))
            # One attempt. Let the accepted safe delivery error propagate, never retry.
            self._events.record_event(event)
        return response
