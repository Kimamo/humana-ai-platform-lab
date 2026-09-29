import httpx
import pytest

from fhir.client import (
    FHIRClient,
    FHIRClientError,
    FHIRNotFoundError,
)
from fhir.config import FHIRConfig


def create_client(handler) -> FHIRClient:
    """
    Creates an FHIR client backed by httpx.MockTransport.

    No real FHIR server is contacted during these tests.
    """
    transport = httpx.MockTransport(handler)

    http_client = httpx.Client(
        transport=transport,
        base_url="http://test-fhir.local",
    )

    config = FHIRConfig(
        base_url="http://test-fhir.local",
        timeout_seconds=10.0,
    )

    return FHIRClient(
        config=config,
        http_client=http_client,
    )


def test_get_patient():

    def handler(request: httpx.Request):

        assert request.url.path == "/Patient/P1001"

        return httpx.Response(
            200,
            json={
                "resourceType": "Patient",
                "id": "P1001",
                "name": [
                    {
                        "given": ["Jane"],
                        "family": "Doe",
                    }
                ],
            },
        )

    client = create_client(handler)

    patient = client.get_patient("P1001")

    assert patient.id == "P1001"
    assert patient.given_name == "Jane"
    assert patient.family_name == "Doe"


def test_patient_not_found():

    def handler(request: httpx.Request):

        return httpx.Response(
            404,
            json={
                "resourceType": "OperationOutcome",
            },
        )

    client = create_client(handler)

    with pytest.raises(FHIRNotFoundError):
        client.get_patient("P9999")


def test_get_patient_medications():

    def handler(request: httpx.Request):

        assert request.url.path == "/MedicationRequest"
        assert request.url.params["patient"] == "P1001"

        return httpx.Response(
            200,
            json={
                "resourceType": "Bundle",
                "type": "searchset",
                "entry": [
                    {
                        "resource": {
                            "resourceType": "MedicationRequest",
                            "id": "med-1",
                            "status": "active",
                            "medicationCodeableConcept": {
                                "text": "Lisinopril 10 mg"
                            },
                            "subject": {
                                "reference": "Patient/P1001"
                            },
                        }
                    },
                    {
                        "resource": {
                            "resourceType": "MedicationRequest",
                            "id": "med-2",
                            "status": "active",
                            "medicationCodeableConcept": {
                                "coding": [
                                    {
                                        "code": "860975",
                                        "display": "Metformin 500 mg",
                                    }
                                ]
                            },
                            "subject": {
                                "reference": "Patient/P1001"
                            },
                        }
                    },
                ],
            },
        )

    client = create_client(handler)

    medications = client.get_medications("P1001")

    assert len(medications) == 2

    assert medications[0].id == "med-1"
    assert medications[0].patient_id == "P1001"
    assert medications[0].medication == "Lisinopril 10 mg"
    assert medications[0].status == "active"

    assert medications[1].id == "med-2"
    assert medications[1].medication == "Metformin 500 mg"


def test_empty_medication_bundle():

    def handler(request: httpx.Request):

        return httpx.Response(
            200,
            json={
                "resourceType": "Bundle",
                "type": "searchset",
                "entry": [],
            },
        )

    client = create_client(handler)

    medications = client.get_medications("P1001")

    assert medications == []


def test_invalid_patient_resource_type():

    def handler(request: httpx.Request):

        return httpx.Response(
            200,
            json={
                "resourceType": "Observation",
                "id": "obs-1",
            },
        )

    client = create_client(handler)

    with pytest.raises(FHIRClientError):
        client.get_patient("P1001")


def test_invalid_medication_bundle_resource_type():

    def handler(request: httpx.Request):

        return httpx.Response(
            200,
            json={
                "resourceType": "Patient",
                "id": "P1001",
            },
        )

    client = create_client(handler)

    with pytest.raises(FHIRClientError):
        client.get_medications("P1001")


def test_fhir_server_error_does_not_expose_response():

    def handler(request: httpx.Request):

        return httpx.Response(
            500,
            json={
                "error": "internal database details",
                "patient_ssn": "123-45-6789",
            },
        )

    client = create_client(handler)

    with pytest.raises(FHIRClientError) as exc:
        client.get_patient("P1001")

    message = str(exc.value)

    assert message == "FHIR patient request failed."
    assert "123-45-6789" not in message
    assert "internal database details" not in message

def test_get_patient_conditions():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/Condition"
        assert request.url.params["patient"] == "P1001"

        return httpx.Response(
            200,
            json={
                "resourceType": "Bundle",
                "type": "searchset",
                "entry": [
                    {
                        "resource": {
                            "resourceType": "Condition",
                            "id": "COND-P1001-001",
                            "code": {
                                "text": "Type 2 diabetes mellitus"
                            },
                        }
                    }
                ],
            },
        )

    transport = httpx.MockTransport(handler)

    with httpx.Client(
        transport=transport,
        base_url="http://test",
    ) as http_client:
        client = FHIRClient(
            base_url="http://test",
            http_client=http_client,
        )

        conditions = client.get_patient_conditions("P1001")

    assert len(conditions) == 1
    assert conditions[0]["resourceType"] == "Condition"
    assert conditions[0]["id"] == "COND-P1001-001"


def test_empty_condition_bundle():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "resourceType": "Bundle",
                "type": "searchset",
                "total": 0,
            },
        )

    transport = httpx.MockTransport(handler)

    with httpx.Client(
        transport=transport,
        base_url="http://test",
    ) as http_client:
        client = FHIRClient(
            base_url="http://test",
            http_client=http_client,
        )

        conditions = client.get_patient_conditions("P1001")

    assert conditions == []


def test_get_patient_observations():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/Observation"
        assert request.url.params["patient"] == "P1001"

        return httpx.Response(
            200,
            json={
                "resourceType": "Bundle",
                "type": "searchset",
                "entry": [
                    {
                        "resource": {
                            "resourceType": "Observation",
                            "id": "BP-P1001-001",
                            "status": "final",
                        }
                    },
                    {
                        "resource": {
                            "resourceType": "Observation",
                            "id": "OBS-P1001-A1C-001",
                            "status": "final",
                        }
                    },
                ],
            },
        )

    transport = httpx.MockTransport(handler)

    with httpx.Client(
        transport=transport,
        base_url="http://test",
    ) as http_client:
        client = FHIRClient(
            base_url="http://test",
            http_client=http_client,
        )

        observations = client.get_patient_observations("P1001")

    assert len(observations) == 2
    assert observations[0]["id"] == "BP-P1001-001"
    assert observations[1]["id"] == "OBS-P1001-A1C-001"

    assert all(
        observation["resourceType"] == "Observation"
        for observation in observations
    )


def test_empty_observation_bundle():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "resourceType": "Bundle",
                "type": "searchset",
                "total": 0,
            },
        )

    transport = httpx.MockTransport(handler)

    with httpx.Client(
        transport=transport,
        base_url="http://test",
    ) as http_client:
        client = FHIRClient(
            base_url="http://test",
            http_client=http_client,
        )

        observations = client.get_patient_observations("P1001")

    assert observations == []

def test_get_resource(http_client):
    http_client.get.return_value.status_code = 200
    http_client.get.return_value.json.return_value = {
        "resourceType": "Observation",
        "id": "OBS-001",
        "valueQuantity": {
            "value": 7.8,
            "unit": "%",
        },
    }

    client = FHIRClient(http_client=http_client)

    result = client.get_resource(
        "Observation",
        "OBS-001",
    )

    assert result["resourceType"] == "Observation"
    assert result["id"] == "OBS-001"
    assert result["valueQuantity"]["value"] == 7.8














