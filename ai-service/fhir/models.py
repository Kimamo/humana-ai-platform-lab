from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Patient:
    id: str
    given_name: str | None = None
    family_name: str | None = None
    resource: dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        return self.resource[key]


@dataclass(frozen=True)
class Medication:
    id: str
    patient_id: str
    medication: str
    status: str | None = None
    resource_type: str = "MedicationRequest"
    resource: dict[str, Any] = field(default_factory=dict)