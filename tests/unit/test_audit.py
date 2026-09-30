"""Unit tests for AuditTrail."""

import pytest
from src.audit.audit_trail import AuditTrail

def test_audit_event_recording():
    audit = AuditTrail()
    assert len(audit.get_events()) == 0

    evt = audit.record_event(
        agent_or_node="TestNode",
        action="TEST_ACTION",
        input_summary="Input test data",
        output_summary="Output result",
        decision="PASSED",
        confidence=0.95,
        warnings=["Test warning"],
        execution_latency_ms=12.4
    )

    assert evt.event_id.startswith("EVT-")
    assert evt.agent_or_node == "TestNode"
    assert evt.confidence == 0.95
    assert len(evt.warnings) == 1
    assert evt.is_synthetic is True

    events = audit.get_events()
    assert len(events) == 1

    node_events = audit.get_events_for_node("TestNode")
    assert len(node_events) == 1
    assert len(audit.get_events_for_node("OtherNode")) == 0

    audit.clear()
    assert len(audit.get_events()) == 0

def test_audit_provenance_and_error_tracking():
    audit = AuditTrail()
    evt = audit.record_event(
        agent_or_node="EligibilityEvidenceAgent",
        action="DETECT_MISSING_LAB",
        input_summary="Patient SYN-PT-009",
        output_summary="eGFR missing",
        decision="ESCALATE_TO_HUMAN_REVIEW",
        confidence=0.60,
        warnings=["Missing critical renal lab"],
        data_provenance="Synthetic Clinical EMR Database",
        execution_latency_ms=8.5,
        errors="DataIncompleteException: eGFR null",
    )

    assert evt.data_provenance == "Synthetic Clinical EMR Database"
    assert evt.errors == "DataIncompleteException: eGFR null"
    assert len(evt.warnings) == 1
    assert evt.timestamp is not None
