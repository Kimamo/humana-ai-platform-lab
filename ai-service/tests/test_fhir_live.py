import pytest

from fhir.client import FHIRClient


FHIR_BASE_URL = "http://localhost:8080/fhir"


@pytest.fixture
def client():
    return FHIRClient(base_url=FHIR_BASE_URL)


def test_live_get_patient(client):
    patient = client.get_patient("P1001")

    assert patient is not None
    assert patient["resourceType"] == "Patient"
    assert patient["id"] == "P1001"

    assert patient["name"][0]["family"] == "TestPatient"
    assert patient["name"][0]["given"][0] == "Alice"


def test_live_get_patient_medications(client):
    bundle = client.get_patient_medications("P1001")

    assert bundle is not None
    assert bundle["resourceType"] == "Bundle"
    assert bundle["total"] >= 1

    medication = bundle["entry"][0]["resource"]

    assert medication["resourceType"] == "MedicationRequest"
    assert medication["subject"]["reference"] == "Patient/P1001"

    assert (
        medication["medicationCodeableConcept"]["text"]
        == "Metformin 500 mg"
    )

def test_patient_summary_includes_fhir_provenance():
    from tools.patient_tools import get_patient_summary
    from fhir.client import FHIRClient

    user = {
        "patient_ids": ["P1001"],
        "scopes": ["patient.read", "medication.read"],
    }

    client = FHIRClient(
        base_url="http://localhost:8080/fhir"
    )

    try:
        summary = get_patient_summary(
            patient_id="P1001",
            user=user,
            fhir_client=client,
        )

        # Patient
        assert (
            summary["patient"]["provenance"]["reference"]
            == "Patient/P1001"
        )

        # Condition
        condition = summary["conditions"][0]

        assert condition["resourceType"] == "Condition"
        assert condition["provenance"]["resource_type"] == "Condition"
        assert condition["provenance"]["resource_id"] == condition["id"]
        assert (
            condition["provenance"]["reference"]
            == f"Condition/{condition['id']}"
        )

        # Medication
        medication = summary["medications"][0]

        assert (
            medication["provenance"]["resource_type"]
            == "MedicationRequest"
        )
        assert (
            medication["provenance"]["resource_id"]
            == medication["id"]
        )
        assert (
            medication["provenance"]["reference"]
            == f"MedicationRequest/{medication['id']}"
        )

        # Observation
        observation = summary["observations"][0]

        assert observation["resourceType"] == "Observation"
        assert (
            observation["provenance"]["resource_id"]
            == observation["id"]
        )
        assert (
            observation["provenance"]["reference"]
            == f"Observation/{observation['id']}"
        )

    finally:
        client.close()

def test_hba1c_provenance_resolves_to_source_resource():
    from tools.patient_tools import get_patient_summary
    from fhir.client import FHIRClient

    user = {
        "patient_ids": ["P1001"],
        "scopes": ["patient.read", "medication.read"],
    }

    client = FHIRClient(
        base_url="http://localhost:8080/fhir"
    )

    try:
        summary = get_patient_summary(
            patient_id="P1001",
            user=user,
            fhir_client=client,
        )

        hba1c = next(
            observation
            for observation in summary["observations"]
            if "a1c"
            in str(observation).lower()
        )

        provenance = hba1c["provenance"]

        assert provenance["resource_type"] == "Observation"
        assert provenance["resource_id"] == hba1c["id"]
        assert (
            provenance["reference"]
            == f"Observation/{hba1c['id']}"
        )

        # Verify the original FHIR resource itself
        assert hba1c["resourceType"] == "Observation"
        assert hba1c["id"] == provenance["resource_id"]

        # Verify this really is the HbA1c observation
        assert hba1c["valueQuantity"]["value"] == 7.8
        assert hba1c["valueQuantity"]["unit"] == "%"

    finally:
        client.close()


