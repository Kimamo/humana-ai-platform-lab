from datetime import datetime, timedelta, timezone
import jwt


SECRET_KEY = (
    "humana-ai-platform-lab-development-secret-key-2026"
)
ALGORITHM = "HS256"

ISSUER = "patient-ai-dev"
AUDIENCE = "patient-ai-api"


def create_access_token(
    user_id: str,
    scopes: list[str],
    roles: list[str]
) -> str:

    now = datetime.now(timezone.utc)

    payload = {
        "sub": user_id,
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + timedelta(minutes=30),
        "scope": " ".join(scopes),
        "roles": roles
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def validate_access_token(token: str) -> dict:

    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
        issuer=ISSUER,
        audience=AUDIENCE
    )
