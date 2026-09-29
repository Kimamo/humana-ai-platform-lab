from unittest.mock import Mock

import pytest

from tools.patient_tools import (
    get_patient,
    get_patient_medications,
    get_patient_conditions,
    get_patient_observations,
)


# ============================================================
# Test helpers
# ============================================================

def make_user(
    patient_ids=None,
    scopes=None,
):
    """
    Minimal authenticated-user representation used by the tool layer.
    Adjust this structure if your authorization.py expects different
    claim names.
    """
    return {
        "sub": "user-123",
        "patient_ids": patient_ids or [],
        "scopes": scopes or [],
    }


# ============================================================
# Patient access
# ============================================================

def test_unauthorized_patient_access_never_calls_fhir():
    fhir_client = Mock()

    user = make_user(
        patient_ids=["P1001"],
        scopes=["patient.read"],
    )

    result = get_patient(
        patient_id="P1002",
        user=user,
        fhir_client=fhir_client,
    )

    fhir_client.get_patient.assert_not_called()

    assert result["error"] == "ACCESS_DENIED"


def test_authorized_patient_access_calls_fhir_once():
    fhir_client = Mock()

    fhir_client.get_patient.return_value = {
        "resourceType": "Patient",
        "id": "P1001",
    }

    user = make_user(
        patient_ids=["P1001"],
        scopes=["patient.read"],
    )

    result = get_patient(
        patient_id="P1001",
        user=user,
        fhir_client=fhir_client,
    )

    fhir_client.get_patient.assert_called_once_with("P1001")

    assert result["resourceType"] == "Patient"
    assert result["id"] == "P1001"


# ============================================================
# Medication access
# ============================================================

def test_missing_medication_scope_never_calls_fhir():
    fhir_client = Mock()

    user = make_user(
        patient_ids=["P1001"],
        scopes=["patient.read"],
    )

    result = get_patient_medications(
        patient_id="P1001",
        user=user,
        fhir_client=fhir_client,
    )

    fhir_client.get_patient_medications.assert_not_called()

    assert result["error"] == "ACCESS_DENIED"


def test_authorized_medication_access_calls_fhir_once():
    fhir_client = Mock()

    fhir_client.get_patient_medications.return_value = {
        "resourceType": "Bundle",
        "entry": [],
    }

    user = make_user(
        patient_ids=["P1001"],
        scopes=[
            "patient.read",
            "medication.read",
        ],
    )

    result = get_patient_medications(
        patient_id="P1001",
        user=user,
        fhir_client=fhir_client,
    )

    fhir_client.get_patient_medications.assert_called_once_with(
        "P1001"
    )

    assert result["resourceType"] == "Bundle"

def test_unauthorized_condition_access_never_calls_fhir():
    class FakeFHIRClient:
        def get_patient_conditions(self, patient_id):
            raise AssertionError(
                "FHIR must not be called for unauthorized access"
            )

    user = {
        "patient_ids": ["P1002"],
        "scopes": ["patient.read"],
    }

    result = get_patient_conditions(
        "P1001",
        user=user,
        fhir_client=FakeFHIRClient(),
    )

    assert result == {"error": "ACCESS_DENIED"}


def test_authorized_condition_access_calls_fhir_once():
    class FakeFHIRClient:
        def __init__(self):
            self.calls = 0

        def get_patient_conditions(self, patient_id):
            self.calls += 1

            return [
                {
                    "resourceType": "Condition",
                    "id": "COND-P1001-001",
                }
            ]

    fhir = FakeFHIRClient()

    user = {
        "patient_ids": ["P1001"],
        "scopes": ["patient.read"],
    }

    result = get_patient_conditions(
        "P1001",
        user=user,
        fhir_client=fhir,
    )

    assert fhir.calls == 1
    assert len(result) == 1
    assert result[0]["id"] == "COND-P1001-001"


def test_unauthorized_observation_access_never_calls_fhir():
    class FakeFHIRClient:
        def get_patient_observations(self, patient_id):
            raise AssertionError(
                "FHIR must not be called for unauthorized access"
            )

    user = {
        "patient_ids": ["P1002"],
        "scopes": ["patient.read"],
    }

    result = get_patient_observations(
        "P1001",
        user=user,
        fhir_client=FakeFHIRClient(),
    )

    assert result == {"error": "ACCESS_DENIED"}


def test_authorized_observation_access_calls_fhir_once():
    class FakeFHIRClient:
        def __init__(self):
            self.calls = 0

        def get_patient_observations(self, patient_id):
            self.calls += 1

            return [
                {
                    "resourceType": "Observation",
                    "id": "OBS-P1001-A1C-001",
                }
            ]

    fhir = FakeFHIRClient()

    user = {
        "patient_ids": ["P1001"],
        "scopes": ["patient.read"],
    }

    result = get_patient_observations(
        "P1001",
        user=user,
        fhir_client=fhir,
    )

    assert fhir.calls == 1
    assert len(result) == 1
    assert result[0]["id"] == "OBS-P1001-A1C-001"

def test_unauthorized_patient_summary_never_calls_fhir(monkeypatch):
    from tools import patient_tools

    class FakeFHIRClient:
        def __init__(self):
            raise AssertionError(
                "FHIRClient must not be created for unauthorized access"
            )

    monkeypatch.setattr(
        patient_tools,
        "FHIRClient",
        FakeFHIRClient,
    )

    user = {
        "sub": "user-001",
        "patient_id": "P1002",
        "scope": "patient.read medication.read",
    }

    result = patient_tools.get_patient_summary(
        patient_id="P1001",
        user=user,
    )

    assert result == {"error": "ACCESS_DENIED"}


def test_missing_medication_scope_blocks_patient_summary(monkeypatch):
    from tools import patient_tools

    class FakeFHIRClient:
        def __init__(self):
            raise AssertionError(
                "FHIRClient must not be created without medication.read"
            )

    monkeypatch.setattr(
        patient_tools,
        "FHIRClient",
        FakeFHIRClient,
    )

    user = {
        "sub": "user-001",
        "patient_id": "P1001",
        "scope": "patient.read",
    }

    result = patient_tools.get_patient_summary(
        patient_id="P1001",
        user=user,
    )

    assert result == {"error": "ACCESS_DENIED"}








