from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.user import UserModel
from models.shop import ShopModel
from tests.lib import login


def _create_owner(test_db: Session, username="shopOwner123"):
    owner = UserModel(username=username, email=f"{username}@example.com", role="owner")
    owner.set_password("mys3cretp2ssw0rd")
    test_db.add(owner)
    test_db.commit()
    test_db.refresh(owner)
    return owner


def _create_admin(test_db: Session, username="adminTest123"):
    admin = UserModel(username=username, email=f"{username}@example.com", role="admin")
    admin.set_password("mys3cretp2ssw0rd")
    test_db.add(admin)
    test_db.commit()
    test_db.refresh(admin)
    return admin


def test_owner_can_create_shop(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    owner = _create_owner(test_db)
    headers = login(test_app, owner.username, "mys3cretp2ssw0rd")

    response = test_app.post(
        "/api/shops",
        json={"name": "Weasleys' Wizard Wheezes", "description": "Joke shop"},
        headers=headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Weasleys' Wizard Wheezes"
    assert data["status"] == "pending"
    assert data["is_authorized"] is False


def test_customer_cannot_create_shop(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    customer = UserModel(username="customer123", email="customer123@example.com", role="user")
    customer.set_password("mys3cretp2ssw0rd")
    test_db.add(customer)
    test_db.commit()

    headers = login(test_app, "customer123", "mys3cretp2ssw0rd")

    response = test_app.post(
        "/api/shops",
        json={"name": "Not Allowed Shop"},
        headers=headers,
    )

    # require_role("owner") should block this
    assert response.status_code == 403


def test_owner_cannot_create_two_shops(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    owner = _create_owner(test_db, username="doubleShopOwner")
    headers = login(test_app, owner.username, "mys3cretp2ssw0rd")

    test_app.post("/api/shops", json={"name": "First Shop"}, headers=headers)
    response = test_app.post("/api/shops", json={"name": "Second Shop"}, headers=headers)

    assert response.status_code == 409


def test_public_shops_list_excludes_pending(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    owner = _create_owner(test_db, username="pendingShopOwner")
    headers = login(test_app, owner.username, "mys3cretp2ssw0rd")
    test_app.post("/api/shops", json={"name": "Still Pending Shop"}, headers=headers)

    # No auth needed — public route
    response = test_app.get("/api/shops")

    assert response.status_code == 200
    names = [shop["name"] for shop in response.json()]
    assert "Still Pending Shop" not in names


def test_admin_can_approve_shop(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    owner = _create_owner(test_db, username="approveTestOwner")
    owner_headers = login(test_app, owner.username, "mys3cretp2ssw0rd")
    create_response = test_app.post(
        "/api/shops", json={"name": "To Be Approved"}, headers=owner_headers
    )
    shop_id = create_response.json()["id"]

    admin = _create_admin(test_db)
    admin_headers = login(test_app, admin.username, "mys3cretp2ssw0rd")

    response = test_app.put(
        f"/api/admin/shops/{shop_id}/status",
        json={"status": "approved"},
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert response.json()["is_authorized"] is True

    # Confirm it now appears in the public list
    public_response = test_app.get("/api/shops")
    names = [shop["name"] for shop in public_response.json()]
    assert "To Be Approved" in names


def test_owner_cannot_approve_own_shop(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    owner = _create_owner(test_db, username="sneakyOwner")
    headers = login(test_app, owner.username, "mys3cretp2ssw0rd")
    create_response = test_app.post(
        "/api/shops", json={"name": "Trying to self-approve"}, headers=headers
    )
    shop_id = create_response.json()["id"]

    # Same owner tries to hit the admin-only route
    response = test_app.put(
        f"/api/admin/shops/{shop_id}/status",
        json={"status": "approved"},
        headers=headers,
    )

    assert response.status_code == 403