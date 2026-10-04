from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.user import UserModel
from tests.lib import login


def test_register_user(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    # Data for registering a new user
    user_data = {
        "username": "registerTestUser123",
        "email": "register-test@example.com",
        "password": "mys3cretp2ssw0rd",
    }

    # Send a POST request to register the user
    response = test_app.post("/api/register", json=user_data)

    # Verify that registration succeeds and returns a token
    assert response.status_code == 201
    data = response.json()
    assert isinstance(data["token"], str)
    assert data["token"]
    assert data["message"] == "Registration successful"
    assert data["role"] == "user"  # defaults to "user" when role is omitted

    # Verify the user was created in the database
    user = (
        test_db.query(UserModel)
        .filter(UserModel.username == user_data["username"])
        .first()
    )
    assert user is not None
    assert user.username == user_data["username"]
    assert user.email == user_data["email"]
    assert user.role == "user"


def test_register_user_as_shop_owner(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    # A user can explicitly register as "owner" (Shop Owner)
    user_data = {
        "username": "ownerTestUser123",
        "email": "owner-test@example.com",
        "password": "mys3cretp2ssw0rd",
        "role": "owner",
    }

    response = test_app.post("/api/register", json=user_data)

    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "owner"

    user = (
        test_db.query(UserModel)
        .filter(UserModel.username == user_data["username"])
        .first()
    )
    assert user.role == "owner"


def test_register_user_cannot_self_register_as_admin(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    # Registering with role "admin" must be rejected — admins are
    # created manually via scripts/create_admin.py, never through
    # public registration.
    user_data = {
        "username": "sneakyAdmin123",
        "email": "sneaky-admin@example.com",
        "password": "mys3cretp2ssw0rd",
        "role": "admin",
    }

    response = test_app.post("/api/register", json=user_data)

    # Pydantic's Literal["user", "owner"] rejects "admin" with a 422
    assert response.status_code == 422

    # Confirm no user was created in the database
    user = (
        test_db.query(UserModel)
        .filter(UserModel.username == user_data["username"])
        .first()
    )
    assert user is None


def test_get_current_user(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    # Create a new mock user in the test database
    user = UserModel(
        username="currentUser123",
        email="current-user@example.com",
    )
    user.set_password("mys3cretp2ssw0rd")
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    # Use the login helper to generate authentication headers
    headers = login(test_app, "currentUser123", "mys3cretp2ssw0rd")

    # Send a GET request for the authenticated user
    response = test_app.get("/api/current_user", headers=headers)

    # Verify the response contains the correct user
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user.id
    assert data["username"] == user.username
    assert data["email"] == user.email
    assert data["role"] == "user"  # default role when not specified