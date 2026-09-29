from typing import Any

import httpx

from fhir.config import FHIRConfig, get_fhir_config
from fhir.models import Medication, Patient


class FHIRClientError(Exception):
    pass


class FHIRNotFoundError(FHIRClientError):
    pass


class FHIRClient:
    def __init__(
        self,
        config: FHIRConfig | None = None,
        http_client: httpx.Client | None = None,
        base_url: str | None = None,
    ):
        if base_url is not None:
            config = FHIRConfig(base_url=base_url)

        self.config = config or get_fhir_config()
        self._owns_client = http_client is None
        self.http_client = http_client or httpx.Client(
            base_url=self.config.base_url,
            timeout=self.config.timeout_seconds,
            headers={
                "Accept": "application/fhir+json",
            },
        )

    def close(self) -> None:
        if self._owns_client:
            self.http_client.close()

    def get_patient(self, patient_id: str) -> Patient:
        response = self.http_client.get(
            f"/Patient/{patient_id}"
        )

        if response.status_code == 404:
            raise FHIRNotFoundError(
                f"Patient {patient_id} was not found."
            )

        self._raise_for_status(
            response,
            "FHIR patient request failed.",
        )
        resource = response.json()
        self._validate_resource(resource, "Patient")

        names = resource.get("name", [])
        given_name = None
        family_name = None
        if names:
            given = names[0].get("given", [])
            given_name = given[0] if given else None
            family_name = names[0].get("family")

        return Patient(
            id=resource["id"],
            given_name=given_name,
            family_name=family_name,
            resource=resource,
        )

    def get_patient_medications(
        self,
        patient_id: str,
    ) -> dict[str, Any]:
        response = self.http_client.get(
            "/MedicationRequest",
            params={"patient": patient_id},
        )
        self._raise_for_status(
            response,
            "FHIR medication request failed.",
        )
        bundle = response.json()
        self._validate_resource(bundle, "Bundle")
        return bundle

    def get_medications(
        self,
        patient_id: str,
    ) -> list[Medication]:
        bundle = self.get_patient_medications(patient_id)
        medications: list[Medication] = []

        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") != "MedicationRequest":
                continue

            medications.append(
                Medication(
                    id=resource["id"],
                    patient_id=patient_id,
                    medication=self._extract_medication_name(resource),
                    status=resource.get("status"),
                    resource_type=resource["resourceType"],
                    resource=resource,
                )
            )

        return medications

    def get_patient_conditions(
        self,
        patient_id: str,
    ) -> list[dict[str, Any]]:
        response = self.http_client.get(
            "/Condition",
            params={"patient": patient_id},
        )
        self._raise_for_status(
            response,
            "FHIR condition request failed.",
        )
        bundle = response.json()
        self._validate_resource(bundle, "Bundle")

        conditions: list[dict[str, Any]] = []
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "Condition":
                conditions.append(resource)

        return conditions

    def get_patient_observations(
        self,
        patient_id: str,
    ) -> list[dict[str, Any]]:
        response = self.http_client.get(
            "/Observation",
            params={"patient": patient_id},
        )
        self._raise_for_status(
            response,
            "FHIR observation request failed.",
        )
        bundle = response.json()
        self._validate_resource(bundle, "Bundle")

        observations: list[dict[str, Any]] = []
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "Observation":
                observations.append(resource)

        return observations

    def get_resource(
        self,
        resource_type: str,
        resource_id: str,
    ) -> dict[str, Any]:
        """Retrieve a FHIR resource by type and ID."""
        response = self.http_client.get(
            f"/{resource_type}/{resource_id}"
        )
        self._raise_for_status(
            response,
            f"Unable to retrieve {resource_type} resource",
        )
        resource = response.json()
        self._validate_resource(resource, resource_type)
        return resource

    @staticmethod
    def _extract_medication_name(
        resource: dict[str, Any]
    ) -> str:
        concept = resource.get(
            "medicationCodeableConcept",
            {},
        )
        if concept.get("text"):
            return concept["text"]

        coding = concept.get("coding", [])
        if coding:
            return (
                coding[0].get("display")
                or coding[0].get("code")
                or "Unknown medication"
            )

        return "Unknown medication"

    @staticmethod
    def _raise_for_status(
        response: httpx.Response,
        message: str,
    ) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise FHIRClientError(message) from exc

    @staticmethod
    def _validate_resource(
        resource: dict[str, Any],
        expected_type: str,
    ) -> None:
        if resource.get("resourceType") != expected_type:
            raise FHIRClientError(
                f"Unexpected FHIR resource type. "
                f"Expected {expected_type}."
            )
