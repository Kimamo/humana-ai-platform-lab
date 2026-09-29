import jwt
import pytest
from datetime import datetime, timedelta, timezone
from security.token_service import (
    create_access_token,
    validate_access_token,
    SECRET_KEY,
    ALGORITHM,
    ISSUER,
    AUDIENCE,
)


def test_valid_token_is_accepted():
    token = create_access_token(
        user_id="dr_smith",
        roles=["clinician"],
        scopes=[
            "patient.read",
            "medication.read",
        ],
    )

    claims = validate_access_token(token)

    assert claims["sub"] == "dr_smith"
    assert claims["roles"] == ["clinician"]
    assert "patient.read" in claims["scope"]
    assert "medication.read" in claims["scope"]


def test_wrong_audience_is_rejected():
    token = jwt.encode(
        {
            "sub": "dr_smith",
            "iss": ISSUER,
            "aud": "wrong-api",
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    with pytest.raises(jwt.InvalidAudienceError):
        validate_access_token(token)



def test_wrong_issuer_is_rejected():
    token = jwt.encode(
        {
            "sub": "dr_smith",
            "iss": "evil-issuer",
            "aud": AUDIENCE,
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    with pytest.raises(jwt.InvalidIssuerError):
        validate_access_token(token)


def test_invalid_signature_is_rejected():
    token = jwt.encode(
        {
            "sub": "dr_smith",
            "iss": ISSUER,
            "aud": AUDIENCE,
        },
        "this-is-a-different-secret-key-that-is-long-enough",
        algorithm=ALGORITHM,
    )

    with pytest.raises(jwt.InvalidSignatureError):
        validate_access_token(token)

def test_expired_token_is_rejected():
    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub": "dr_smith",
            "iss": ISSUER,
            "aud": AUDIENCE,
            "iat": now - timedelta(hours=1),
            "exp": now - timedelta(minutes=30),
            "scope": "patient.read medication.read",
            "roles": ["clinician"],
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        validate_access_token(token)




