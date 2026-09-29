from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from api import app


client = TestClient(app)


def auth_header(token: str):
    return {
        "Authorization": f"Bearer {token}"
    }


def test_chat_authorized_patient_request_reaches_fhir(valid_token):
    """
    Authorized patient request should reach the FHIR layer.
    """

    with patch("tools.patient_tools.FHIRClient") as mock_fhir_class:
        mock_fhir = Mock()

        mock_fhir.get_patient.return_value = {
            "resourceType": "Patient",
            "id": "P1001",
            "name": [
                {
                    "given": ["Jane"],
                    "family": "Doe"
                }
            ]
        }

        mock_fhir_class.return_value = mock_fhir

        response = client.post(
            "/chat",
            headers=auth_header(valid_token),
            json={
                "message": "Retrieve patient P1001."
            }
        )

        assert response.status_code == 200

        mock_fhir.get_patient.assert_called_once_with("P1001")


def test_chat_unauthorized_patient_request_never_reaches_fhir(
    valid_token
):
    """
    Patient-level authorization must fail BEFORE FHIR access.
    """

    with patch("tools.patient_tools.FHIRClient") as mock_fhir_class:
        mock_fhir = Mock()
        mock_fhir_class.return_value = mock_fhir

        response = client.post(
            "/chat",
            headers=auth_header(valid_token),
            json={
                "message": "Retrieve patient P9999."
            }
        )

        assert response.status_code == 200

        mock_fhir.get_patient.assert_not_called()
        mock_fhir.get_patient_medications.assert_not_called()

        body = response.json()

        assert "denied" in body["response"].lower()


def test_chat_authorized_medication_request_reaches_fhir(
    valid_token
):
    """
    Authorized medication request should reach the FHIR layer.
    """

    with patch("tools.patient_tools.FHIRClient") as mock_fhir_class:
        mock_fhir = Mock()

        mock_fhir.get_patient_medications.return_value = {
            "resourceType": "Bundle",
            "type": "searchset",
            "entry": [
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "MED-001",
                        "status": "active",
                    }
                }
            ]
        }

        mock_fhir_class.return_value = mock_fhir

        response = client.post(
            "/chat",
            headers=auth_header(valid_token),
            json={
                "message":
                    "What medications is patient P1001 taking?"
            }
        )

        assert response.status_code == 200

        mock_fhir.get_patient_medications.assert_called_once_with(
            "P1001"
        )


def test_chat_missing_medication_scope_never_reaches_fhir(
    token_without_medication_scope
):
    """
    Missing medication scope must stop execution before FHIR.
    """

    with patch("tools.patient_tools.FHIRClient") as mock_fhir_class:
        mock_fhir = Mock()
        mock_fhir_class.return_value = mock_fhir

        response = client.post(
            "/chat",
            headers=auth_header(token_without_medication_scope),
            json={
                "message":
                    "What medications is patient P1001 taking?"
            }
        )

        assert response.status_code == 200

        mock_fhir.get_patient_medications.assert_not_called()

        body = response.json()

        assert "denied" in body["response"].lower()