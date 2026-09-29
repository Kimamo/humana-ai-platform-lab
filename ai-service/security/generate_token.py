try:
    from security.token_service import create_access_token
except ModuleNotFoundError:
    from token_service import create_access_token


def generate_token():
    token = create_access_token(
        user_id="dr_smith",
        scopes=[
            "patient.read",
            "medication.read",
        ],
        roles=["clinician"],
    )

    print("\nBearer token:\n")
    print(token)
    print()


if __name__ == "__main__":
    generate_token()