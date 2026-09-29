import uuid

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jwt import InvalidTokenError
from pydantic import BaseModel

from app import run_agent
from security.token_service import validate_access_token


class ChatRequest(BaseModel):
    message: str


app = FastAPI(
    title="Patient AI Service"
)

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    )
) -> dict:
    try:
        return validate_access_token(
            credentials.credentials
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )


@app.post("/chat")
def chat(
    request: ChatRequest,
    claims: dict = Depends(get_current_user),
):
    user_id = claims["sub"]
    request_id = str(uuid.uuid4())
    scopes = claims.get(
        "scope",
        ""
    ).split()

    response = run_agent(
        user_id=user_id,
        prompt=request.message,
        scopes=scopes,
    )

    return {
        "response": response,
        "request_id": request_id,
    }


@app.get("/me")
def get_me(
    claims: dict = Depends(get_current_user)
):

    return {
        "user_id": claims["sub"],
        "roles": claims.get("roles", []),
        "scopes": claims.get(
            "scope",
            ""
        ).split()
    }
