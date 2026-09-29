from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import Any


AUDIT_LOG_PATH = Path(
    os.getenv("AUDIT_LOG_PATH", "logs/audit.jsonl")
)

_write_lock = Lock()

logger = logging.getLogger("security.audit")


SENSITIVE_FIELDS = {
    "authorization",
    "access_token",
    "refresh_token",
    "token",
    "jwt",
    "password",
    "prompt",
    "message",
    "tool_result",
    "patient_data",
    "medications",
}


class AuditEventType(str, Enum):
    AUTHORIZATION_DENIED = "AUTHORIZATION_DENIED"
    AUTHORIZATION_ALLOWED = "AUTHORIZATION_ALLOWED"
    TOOL_EXECUTION_SUCCESS = "TOOL_EXECUTION_SUCCESS"
    TOOL_EXECUTION_FAILURE = "TOOL_EXECUTION_FAILURE"


class AuditDecision(str, Enum):
    DENY = "DENY"
    ALLOW = "ALLOW"
    ERROR = "ERROR"


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]"
            if str(key).lower() in SENSITIVE_FIELDS
            else _sanitize(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [_sanitize(item) for item in value]

    if isinstance(value, tuple):
        return [_sanitize(item) for item in value]

    return value


def _calculate_hash(event: dict[str, Any]) -> str:
    hashable_event = {
        key: value
        for key, value in event.items()
        if key != "hash"
    }
    serialized = json.dumps(
        hashable_event,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()


def _read_events() -> list[dict[str, Any]]:
    if not AUDIT_LOG_PATH.exists():
        return []

    try:
        content = AUDIT_LOG_PATH.read_text(
            encoding="utf-8"
        ).strip()
        return json.loads(content) if content else []
    except (json.JSONDecodeError, OSError):
        return []


def audit_event(
    *,
    event_type: str | AuditEventType,
    user_id: str,
    tool_name: str | None = None,
    patient_id: str | None = None,
    outcome: str | None = None,
    reason: str | None = None,
    request_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    decision: str | AuditDecision | None = None,
    tool: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    required_scope: str | None = None,
    **_: Any,
) -> dict[str, Any]:
    event_type_value = (
        event_type.value
        if isinstance(event_type, AuditEventType)
        else str(event_type)
    )
    decision_value = (
        decision.value
        if isinstance(decision, AuditDecision)
        else str(decision).upper()
        if decision is not None
        else None
    )

    effective_tool_name = tool_name or tool
    effective_patient_id = patient_id or resource_id
    effective_resource_type = resource_type or (
        "patient" if effective_patient_id else None
    )

    if outcome is None and decision_value is not None:
        outcome = {
            "DENY": "DENIED",
            "ALLOW": "ALLOWED",
            "ERROR": "ERROR",
        }.get(decision_value, decision_value)

    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": _utc_timestamp(),
        "request_id": request_id,
        "event_type": event_type_value,
        "user_id": user_id,
        "tool_name": effective_tool_name,
        "resource_type": effective_resource_type,
        "resource_id": effective_patient_id,
        "outcome": outcome,
        "reason": reason,
        "required_scope": required_scope,
        "metadata": _sanitize(metadata or {}),
    }
    event = {
        key: value
        for key, value in event.items()
        if value is not None
    }

    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(
        event,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    with _write_lock:
        with AUDIT_LOG_PATH.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(line + "\n")

    logger.info(
        "security_audit event_type=%s request_id=%s user_id=%s",
        event_type_value,
        request_id,
        user_id,
    )
    return event


def write_audit_event(
    *,
    request_id: str,
    event_type: str,
    user_id: str,
    tool_name: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    outcome: str,
    reason: str,
    required_scope: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    with _write_lock:
        events = _read_events()
        previous_hash = events[-1].get("hash") if events else None
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": _utc_timestamp(),
            "request_id": request_id,
            "event_type": event_type,
            "user_id": user_id,
            "tool_name": tool_name,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "outcome": outcome,
            "reason": reason,
            "required_scope": required_scope,
            "metadata": _sanitize(metadata or {}),
            "previous_hash": previous_hash,
        }
        event["hash"] = _calculate_hash(event)
        events.append(event)
        AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        AUDIT_LOG_PATH.write_text(
            json.dumps(events, indent=2),
            encoding="utf-8",
        )
        return event


def verify_audit_chain() -> bool:
    events = _read_events()
    previous_hash = None

    for event in events:
        if event.get("previous_hash") != previous_hash:
            return False
        if event.get("hash") != _calculate_hash(event):
            return False
        previous_hash = event.get("hash")

    return True


__all__ = [
    "AUDIT_LOG_PATH",
    "AuditEventType",
    "AuditDecision",
    "audit_event",
    "write_audit_event",
    "verify_audit_chain",
    "SENSITIVE_FIELDS",
    "_sanitize",
]
