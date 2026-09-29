USER_PATIENT_ACCESS = {
    "dr_smith": {"P1001"},
    "dr_jones": {"P1002"}
}


class AuthorizationError(Exception):
    pass


def authorize_patient_access(
    user_id: str,
    patient_id: str
) -> None:

    allowed_patients = USER_PATIENT_ACCESS.get(
        user_id,
        set()
    )

    if patient_id not in allowed_patients:
        raise AuthorizationError(
            f"User {user_id} is not authorized "
            f"to access patient {patient_id}"
        )