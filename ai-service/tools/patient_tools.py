from typing import Any

from fhir.client import FHIRClient


PATIENTS = {
    "P1001": {
        "name": "Synthetic Patient A",
        "age": 52,
        "medications": [
            {
                "name": "Lisinopril",
                "dosage": "10 mg",
                "frequency": "Once daily"
            },
            {
                "name": "Atorvastatin",
                "dosage": "20 mg",
                "frequency": "Once daily"
            }
        ],

        "appointments": [
            {
                "date": "2026-10-12",
                "type": "Primary care follow-up"
            }
        ]
    },

    "P1002": {
        "name": "Synthetic Patient B",
        "age": 67,

        "visits": [
            {
                "date": "2026-09-01",
                "reason": "Blood pressure follow-up"
            }
        ],

        "medications": [
            {
                "name": "Metformin",
                "dosage": "500 mg",
                "frequency": "Twice daily"
            }
        ],

        "appointments": []
    }
}


def _has_patient_access(
    patient_id: str,
    user: dict[str, Any] | None,
    required_scope: str,
) -> bool:
    if user is None:
        return True

    patient_ids = user.get("patient_ids", [])
    scopes = user.get("scopes", [])
    if isinstance(scopes, str):
        scopes = scopes.split()

    return (
        patient_id in patient_ids
        and required_scope in scopes
    )


class _LocalFhirClient:
    def get_patient(self, patient_id: str) -> dict:
        patient = PATIENTS.get(patient_id)
        if patient is None:
            return {"error": "Patient not found"}
        return {
            "resourceType": "Patient",
            "id": patient_id,
            "name": patient["name"],
            "age": patient["age"],
        }

    def get_patient_medications(self, patient_id: str) -> dict:
        patient = PATIENTS.get(patient_id)
        if patient is None:
            return {"error": "Patient not found"}
        return {
            "resourceType": "Bundle",
            "entry": patient["medications"],
        }


_local_fhir_client = _LocalFhirClient()


def get_patient(
    patient_id: str,
    user: dict[str, Any] | None = None,
    fhir_client: Any = None,
) -> dict:
    """Get a patient record after checking patient read access."""
    if not _has_patient_access(
        patient_id,
        user,
        "patient.read",
    ):
        return {"error": "ACCESS_DENIED"}

    client = fhir_client or FHIRClient()
    return client.get_patient(patient_id)


def get_patient_visits(patient_id: str) -> dict:
    """Get visit history for a synthetic patient."""

    patient = PATIENTS.get(patient_id)

    if patient is None:
        return {"error": "Patient not found"}

    return {
        "patient_id": patient_id,
        "visits": patient["visits"]
    }


def get_patient_medications(
    patient_id: str,
    user: dict[str, Any] | None = None,
    fhir_client: Any = None,
) -> dict:
    """Get current medications for a synthetic patient."""

    if not _has_patient_access(
        patient_id,
        user,
        "medication.read",
    ):
        return {"error": "ACCESS_DENIED"}

    if fhir_client is not None:
        return fhir_client.get_patient_medications(patient_id)

    if FHIRClient is not None:
        return FHIRClient().get_patient_medications(patient_id)

    patient = PATIENTS.get(patient_id)

    if patient is None:
        return {"error": "Patient not found"}

    return {
        "patient_id": patient_id,
        "medications": patient["medications"]
    }


def get_patient_conditions(
    patient_id: str,
    user: dict[str, Any] | None = None,
    fhir_client: Any = None,
) -> list[dict] | dict:
    """Get patient conditions after checking patient read access."""

    if not _has_patient_access(
        patient_id,
        user,
        "patient.read",
    ):
        return {"error": "ACCESS_DENIED"}

    client = fhir_client or FHIRClient()
    return client.get_patient_conditions(patient_id)


def get_patient_observations(
    patient_id: str,
    user: dict[str, Any] | None = None,
    fhir_client: Any = None,
) -> list[dict] | dict:
    """Get patient observations after checking patient read access."""

    if not _has_patient_access(
        patient_id,
        user,
        "patient.read",
    ):
        return {"error": "ACCESS_DENIED"}

    client = fhir_client or FHIRClient()
    return client.get_patient_observations(patient_id)


def get_patient_appointments(patient_id: str) -> dict:
    """Get upcoming appointments for a synthetic patient."""

    patient = PATIENTS.get(patient_id)

    if patient is None:
        return {"error": "Patient not found"}

    return {
        "patient_id": patient_id,
        "appointments": patient["appointments"]
    }


def get_patient_summary(
    patient_id: str,
    user: dict[str, Any] | None = None,
    fhir_client: Any = None,
) -> dict:
    """
    Retrieve an authorized clinical summary for a patient.

    Authorization is checked before any FHIR request is made.
    """

    # Patient-level authorization
    if not _has_patient_access(
        patient_id,
        user,
        "patient.read",
    ):
        return {"error": "ACCESS_DENIED"}

    # Medication access requires its own scope
    if not _has_patient_access(
        patient_id,
        user,
        "medication.read",
    ):
        return {"error": "ACCESS_DENIED"}

    client = fhir_client or FHIRClient()

    patient = client.get_patient(patient_id)
    conditions = client.get_patient_conditions(patient_id)
    medications = client.get_medications(patient_id)
    observations = client.get_patient_observations(patient_id)

    return {
        "patient": {
            "id": patient.id,
            "given_name": patient.given_name,
            "family_name": patient.family_name,
            "provenance": {
                "resource_type": "Patient",
                "resource_id": patient.id,
                "reference": f"Patient/{patient.id}",
            },
        },
        "conditions": [
            {
                **condition,
                "provenance": {
                    "resource_type": condition["resourceType"],
                    "resource_id": condition["id"],
                    "reference": (
                        f'{condition["resourceType"]}/{condition["id"]}'
                    ),
                },
            }
            for condition in conditions
        ],
        "medications": [
            {
                "id": medication.id,
                "patient_id": medication.patient_id,
                "medication": medication.medication,
                "status": medication.status,
                "provenance": {
                    "resource_type": medication.resource_type,
                    "resource_id": medication.id,
                    "reference": (
                        f"{medication.resource_type}/{medication.id}"
                    ),
                },
            }
            for medication in medications
        ],
        "observations": [
            {
                **observation,
                "provenance": {
                    "resource_type": observation["resourceType"],
                    "resource_id": observation["id"],
                    "reference": (
                        f'{observation["resourceType"]}/{observation["id"]}'
                    ),
                },
            }
            for observation in observations
        ],
    }


def _attach_tool_interface(function):
    function.name = function.__name__
    function.invoke = lambda arguments: function(**arguments)
    return function


get_patient_summary = _attach_tool_interface(
    get_patient_summary
)
get_patient = _attach_tool_interface(get_patient)

get_patient_visits = _attach_tool_interface(
    get_patient_visits
)

get_patient_medications = _attach_tool_interface(
    get_patient_medications
)

get_patient_conditions = _attach_tool_interface(
    get_patient_conditions
)

get_patient_observations = _attach_tool_interface(
    get_patient_observations
)

get_patient_appointments = _attach_tool_interface(
    get_patient_appointments
)
