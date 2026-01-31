from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.models import User, UserCreate, UserUpdate
from tests.utils.utils import random_email, random_lower_string


def user_authentication_headers(*, client: TestClient, email: str, password: str) -> dict[str, str]:
    data = {"username": email, "password": password}

    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=data)
    response = r.json()
    auth_token = response["access_token"]
    return {"Authorization": f"Bearer {auth_token}"}


def create_random_user(session: Session) -> User:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    return crud.create_user(session=session, user_create=user_in)


def authentication_token_from_email(*, client: TestClient, email: str, session: Session) -> dict[str, str]:
    """Return a valid token for the user with given email.

    If the user doesn't exist it is created first.

    Raises:
        Exception: If the user ID is not set after creation.
    """
    password = random_lower_string()
    user = crud.get_user_by_email(session=session, email=email)
    if not user:
        user_in_create = UserCreate(email=email, password=password)
        user = crud.create_user(session=session, user_create=user_in_create)
    else:
        user_in_update = UserUpdate(password=password)
        if not user.id:
            msg = "User id not set"
            raise Exception(msg)
        user = crud.update_user(session=session, db_user=user, user_in=user_in_update)

    return user_authentication_headers(client=client, email=email, password=password)
