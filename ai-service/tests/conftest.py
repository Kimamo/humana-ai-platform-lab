import pytest
from unittest.mock import Mock

from security.token_service import create_access_token


@pytest.fixture
def http_client():
    client = Mock()
    response = Mock()
    response.raise_for_status.return_value = None
    client.get.return_value = response
    return client


@pytest.fixture
def valid_token():
    return create_access_token(
        user_id="dr_smith",
        roles=["clinician"],
        scopes=["patient.read", "medication.read"],
    )


@pytest.fixture
def token_without_medication_scope():
    return create_access_token(
        user_id="dr_smith",
        roles=["clinician"],
        scopes=["patient.read"],
    )
