import json

from security import audit


def test_audit_event_is_persisted(tmp_path, monkeypatch):

    audit_file = tmp_path / "audit.jsonl"

    monkeypatch.setattr(
        audit,
        "AUDIT_LOG_PATH",
        audit_file,
    )

    event = audit.audit_event(
        event_type="AUTHORIZATION_DENIED",
        user_id="dr_smith",
        tool_name="get_patient_medications",
        patient_id="P1002",
        outcome="DENIED",
        reason="PATIENT_ACCESS_DENIED",
        request_id="req-123",
    )

    assert audit_file.exists()

    lines = audit_file.read_text().splitlines()

    assert len(lines) == 1

    stored = json.loads(lines[0])

    assert stored["event_id"] == event["event_id"]
    assert stored["request_id"] == "req-123"
    assert stored["user_id"] == "dr_smith"
    assert stored["tool_name"] == "get_patient_medications"
    assert stored["resource_id"] == "P1002"
    assert stored["outcome"] == "DENIED"


def test_sensitive_metadata_is_redacted(
    tmp_path,
    monkeypatch,
):

    audit_file = tmp_path / "audit.jsonl"

    monkeypatch.setattr(
        audit,
        "AUDIT_LOG_PATH",
        audit_file,
    )

    audit.audit_event(
        event_type="SECURITY_TEST",
        user_id="dr_smith",
        request_id="req-456",
        metadata={
            "authorization": "Bearer secret-token",
            "prompt": "private prompt",
            "patient_data": {
                "name": "Sensitive Patient"
            },
            "safe_field": "allowed",
        },
    )

    stored = json.loads(
        audit_file.read_text().splitlines()[0]
    )

    metadata = stored["metadata"]

    assert metadata["authorization"] == "[REDACTED]"
    assert metadata["prompt"] == "[REDACTED]"
    assert metadata["patient_data"] == "[REDACTED]"
    assert metadata["safe_field"] == "allowed"



def test_audit_events_are_hash_chained(tmp_path, monkeypatch):

    log_file = tmp_path / "audit_log.json"
    monkeypatch.setattr(audit, "AUDIT_LOG_PATH", log_file)

    first = audit.write_audit_event(
        request_id="req-1",
        event_type="AUTHORIZATION_ALLOWED",
        user_id="dr_smith",
        tool_name="get_patient_medications",
        resource_type="patient",
        resource_id="P1001",
        outcome="ALLOWED",
        reason="AUTHORIZED",
        required_scope="medication.read",
    )

    second = audit.write_audit_event(
        request_id="req-1",
        event_type="TOOL_EXECUTION_SUCCESS",
        user_id="dr_smith",
        tool_name="get_patient_medications",
        resource_type="patient",
        resource_id="P1001",
        outcome="ALLOWED",
        reason="TOOL_EXECUTED",
        required_scope="medication.read",
    )

    assert first["previous_hash"] is None
    assert first["hash"] is not None

    assert second["previous_hash"] == first["hash"]
    assert second["hash"] is not None

    assert audit.verify_audit_chain() is True

def test_audit_chain_detects_tampering(tmp_path, monkeypatch):

    log_file = tmp_path / "audit_log.json"
    monkeypatch.setattr(audit, "AUDIT_LOG_PATH", log_file)

    audit.write_audit_event(
        request_id="req-1",
        event_type="AUTHORIZATION_DENIED",
        user_id="dr_smith",
        tool_name="get_patient_medications",
        resource_type="patient",
        resource_id="P1002",
        outcome="DENIED",
        reason="PATIENT_ACCESS_DENIED",
        required_scope="medication.read",
    )

    assert audit.verify_audit_chain() is True

    events = json.loads(log_file.read_text())

    # Simulate an attacker changing the audit history.
    events[0]["outcome"] = "ALLOWED"

    log_file.write_text(json.dumps(events, indent=2))

    assert audit.verify_audit_chain() is False