import httpx

FHIR_BASE_URL = "http://localhost:8080/fhir"

patient = {
    "resourceType": "Patient",
    "id": "P1001",
    "active": True,
    "name": [
        {
            "use": "official",
            "family": "TestPatient",
            "given": ["Alice"],
        }
    ],
    "gender": "female",
    "birthDate": "1985-04-12",
}

medication = {
    "resourceType": "MedicationRequest",
    "id": "MED-P1001-001",
    "status": "active",
    "intent": "order",
    "medicationCodeableConcept": {
        "coding": [
            {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "860975",
                "display": "Metformin 500 MG Oral Tablet",
            }
        ],
        "text": "Metformin 500 mg",
    },
    "subject": {
        "reference": "Patient/P1001",
    },
    "dosageInstruction": [
        {
            "text": "Take one tablet twice daily with meals."
        }
    ],
}
condition = {
    "resourceType": "Condition",
    "id": "COND-P1001-001",
    "clinicalStatus": {
        "coding": [
            {
                "system": (
                    "http://terminology.hl7.org/CodeSystem/"
                    "condition-clinical"
                ),
                "code": "active",
                "display": "Active",
            }
        ]
    },
    "verificationStatus": {
        "coding": [
            {
                "system": (
                    "http://terminology.hl7.org/CodeSystem/"
                    "condition-ver-status"
                ),
                "code": "confirmed",
                "display": "Confirmed",
            }
        ]
    },
    "category": [
        {
            "coding": [
                {
                    "system": (
                        "http://terminology.hl7.org/CodeSystem/"
                        "condition-category"
                    ),
                    "code": "problem-list-item",
                    "display": "Problem List Item",
                }
            ]
        }
    ],
    "code": {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "44054006",
                "display": "Type 2 diabetes mellitus",
            }
        ],
        "text": "Type 2 diabetes mellitus",
    },
    "subject": {
        "reference": "Patient/P1001",
    },
    "onsetDateTime": "2024-03-15",
}

observation = {
    "resourceType": "Observation",
    "id": "OBS-P1001-A1C-001",
    "status": "final",
    "category": [
        {
            "coding": [
                {
                    "system": (
                        "http://terminology.hl7.org/CodeSystem/"
                        "observation-category"
                    ),
                    "code": "laboratory",
                    "display": "Laboratory",
                }
            ]
        }
    ],
    "code": {
        "coding": [
            {
                "system": "http://loinc.org",
                "code": "4548-4",
                "display": "Hemoglobin A1c/Hemoglobin.total in Blood",
            }
        ],
        "text": "Hemoglobin A1c",
    },
    "subject": {
        "reference": "Patient/P1001",
    },
    "effectiveDateTime": "2026-09-20T09:30:00Z",
    "valueQuantity": {
        "value": 7.8,
        "unit": "%",
        "system": "http://unitsofmeasure.org",
        "code": "%",
    },
}

def put_resource(resource):
    resource_type = resource["resourceType"]
    resource_id = resource["id"]

    url = f"{FHIR_BASE_URL}/{resource_type}/{resource_id}"

    response = httpx.put(
        url,
        json=resource,
        headers={"Content-Type": "application/fhir+json"},
        timeout=10.0,
    )

    response.raise_for_status()

    print(
        f"Seeded {resource_type}/{resource_id} "
        f"-> HTTP {response.status_code}"
    )


if __name__ == "__main__":
    put_resource(patient)
    put_resource(medication)
    put_resource(condition)
    put_resource(observation)

    print("\nFHIR seed completed.")