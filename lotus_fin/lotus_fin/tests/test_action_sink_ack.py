"""Required sink policy and acknowledgment regression tests (A16); no ERP."""

import io
import logging
import threading
import uuid
import pytest
from lotus_fin.application.port.i_action_events import (
    ActionEvent, ActionEventStage, ActionEventDeliveryError,
)
from lotus_fin.infrastructure.observability.action_events import SafeStructuredActionEvents


def event():
    return ActionEvent(correlation_id=str(uuid.uuid4()), request_id=str(uuid.uuid4()),
                       capability="invoice.context", stage=ActionEventStage.AUTH_CHECK)


def adapter(handler):
    log = logging.Logger("test.required.sink", logging.INFO)
    log.propagate = False
    log.addHandler(handler)
    return SafeStructuredActionEvents(log), log


@pytest.mark.parametrize("policy", ["logger", "stream", "generic"])
def test_filter_rejection_never_emits_or_counts(policy):
    stream = io.StringIO()
    emissions, calls = [], []

    class Generic(logging.Handler):
        def emit(self, record):
            emissions.append(record)

    h = Generic() if policy == "generic" else logging.StreamHandler(stream)
    a, log = adapter(h)

    def deny(record):
        calls.append(record)
        return False

    (log if policy == "logger" else h).addFilter(deny)
    try:
        with pytest.raises(ActionEventDeliveryError):
            a.record_event(event())
        assert len(calls) == 1
        assert stream.getvalue() == "" and emissions == []
        assert a.recorded_events == []
    finally:
        h.close()


@pytest.mark.parametrize("ack", [None, 0, -1, "short", False, True])
def test_unacknowledged_or_short_write_is_not_delivery(ack):
    flushes = []

    class Stream:
        def write(self, message):
            return len(message) - 1 if ack == "short" else ack

        def flush(self):
            flushes.append(True)

    h = logging.StreamHandler(Stream())
    a, _ = adapter(h)
    try:
        with pytest.raises(ActionEventDeliveryError):
            a.record_event(event())
        assert a.recorded_events == []
        assert flushes == []
    finally:
        # close does not flush a StreamHandler.
        h.close()


@pytest.mark.parametrize("kind", ["generic", "custom_emit", "custom_handle", "custom_logger"])
def test_unsupported_delivery_fails_closed(kind):
    stream = io.StringIO()

    class Generic(logging.Handler):
        def emit(self, record):
            raise AssertionError("Unsupported sink must not emit")

    h = Generic() if kind == "generic" else logging.StreamHandler(stream)
    if kind == "custom_emit":
        h.emit = lambda record: None
    if kind == "custom_handle":
        h.handle = lambda record: False
    a, log = adapter(h)
    if kind == "custom_logger":
        log.handle = lambda record: None
    try:
        with pytest.raises(ActionEventDeliveryError):
            a.record_event(event())
        assert not a.recorded_events and stream.getvalue() == ""
    finally:
        h.close()


def test_flush_failure_does_not_count_delivery():
    class Stream(io.StringIO):
        def flush(self):
            raise OSError("PRIVATE_SINK_CANARY")

    h = logging.StreamHandler(Stream())
    a, _ = adapter(h)
    try:
        with pytest.raises(ActionEventDeliveryError, match="Required action audit delivery failed") as exc:
            a.record_event(event())
        assert not a.recorded_events
        assert exc.value.__cause__ is None and exc.value.__suppress_context__
    finally:
        h.close()


def test_all_handler_filters_precede_any_write():
    stream = io.StringIO()
    first, denied = logging.StreamHandler(stream), logging.StreamHandler(io.StringIO())
    a, log = adapter(first)
    denied.addFilter(lambda record: False)
    log.addHandler(denied)
    try:
        with pytest.raises(ActionEventDeliveryError):
            a.record_event(event())
        assert stream.getvalue() == "" and a.recorded_events == []
    finally:
        first.close()
        denied.close()


def test_one_suppressed_required_handler_prevents_all_delivery():
    stream = io.StringIO()
    first, suppressed = logging.StreamHandler(stream), logging.StreamHandler(io.StringIO())
    a, log = adapter(first)
    suppressed.setLevel(logging.WARNING)
    log.addHandler(suppressed)
    try:
        with pytest.raises(ActionEventDeliveryError):
            a.record_event(event())
        assert not a.recorded_events and stream.getvalue() == ""
    finally:
        first.close()
        suppressed.close()


def test_shared_handler_serializes_writes_without_patching_callback():
    entered, release, second_started, second_done = [threading.Event() for _ in range(4)]
    writes, outcomes = [], {}

    class Stream:
        def write(self, message):
            if threading.current_thread().name == "sink-A":
                entered.set()
                assert release.wait(3)
                writes.append(message)
                return len(message)
            raise OSError("PRIVATE_CONCURRENT_SINK_OUTAGE")

        def flush(self):
            pass

    h = logging.StreamHandler(Stream())
    a, log = adapter(h)
    adapters = dict(A=a, B=SafeStructuredActionEvents(log))
    original = h.handleError

    def worker(name):
        if name == "B":
            second_started.set()
        try:
            adapters[name].record_event(event())
            outcomes[name] = "acknowledged"
        except ActionEventDeliveryError:
            outcomes[name] = "failed"
        finally:
            if name == "B":
                second_done.set()

    threads = [threading.Thread(target=worker, args=(name,), name="sink-" + name) for name in "AB"]
    try:
        threads[0].start()
        assert entered.wait(3)
        threads[1].start()
        assert second_started.wait(3)
        assert not second_done.wait(0.1)
        release.set()
        for thread in threads:
            thread.join(5)
        assert all(not thread.is_alive() for thread in threads)
        assert outcomes == dict(A="acknowledged", B="failed")
        assert len(writes) == 1 and len(a.recorded_events) == 1 and not adapters["B"].recorded_events
        assert h.handleError == original
    finally:
        release.set()
        for thread in threads:
            if thread.ident is not None:
                thread.join(5)
        h.close()
