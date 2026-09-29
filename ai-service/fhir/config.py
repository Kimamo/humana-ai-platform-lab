import os
from dataclasses import dataclass


@dataclass(frozen=True)
class FHIRConfig:
    base_url: str
    timeout_seconds: float = 10.0


def get_fhir_config() -> FHIRConfig:
    return FHIRConfig(
        base_url=os.getenv(
            "FHIR_BASE_URL",
            "http://localhost:8080/fhir"
        ).rstrip("/"),
        timeout_seconds=float(
            os.getenv("FHIR_TIMEOUT_SECONDS", "10")
        ),
    )