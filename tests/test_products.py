# tests/test_products.py

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.user import UserModel
from models.shop import ShopModel
from models.product import ProductModel
from tests.lib import login


def _create_owner(test_db: Session, username="productOwner123"):
    owner = UserModel(username=username, email=f"{username}@example.com", role="owner")
    owner.set_password("mys3cretp2ssw0rd")
    test_db.add(owner)
    test_db.commit()
    test_db.refresh(owner)
    return owner


def _create_admin(test_db: Session, username="productAdmin123"):
    admin = UserModel(username=username, email=f"{username}@example.com", role="admin")
    admin.set_password("mys3cretp2ssw0rd")
    test_db.add(admin)
    test_db.commit()
    test_db.refresh(admin)
    return admin


def _create_customer(test_db: Session, username="productCustomer123"):
    customer = UserModel(username=username, email=f"{username}@example.com", role="user")
    customer.set_password("mys3cretp2ssw0rd")
    test_db.add(customer)
    test_db.commit()
    test_db.refresh(customer)
    return customer


def _create_shop(test_db: Session, owner: UserModel, status="pending", name="Test Shop"):
    shop = ShopModel(owner_id=owner.id, name=name, description="A shop", status=status)
    test_db.add(shop)
    test_db.commit()
    test_db.refresh(shop)
    return shop


def _sample_product_payload(name="Fainting Fancies"):
    return {
        "name": name,
        "category": "Skiving Snackboxes",
        "description": "Turns you pale and makes you faint on command.",
        "price_gbp": "3.50",
        "stock": 10,
        "image_urls": [],
        "is_banned_at_hogwarts": True,
    }


# ---------------------------------------------------------------------
# Shop-approval gate (US13)
# ---------------------------------------------------------------------

def test_owner_cannot_add_product_if_shop_not_approved(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    owner = _create_owner(test_db, username="pendingShopOwner2")
    _create_shop(test_db, owner, status="pending")  # not approved yet
    headers = login(test_app, owner.username, "mys3cretp2ssw0rd")

    response = test_app.post(
        "/api/products",
        json=_sample_product_payload(),
        headers=headers,
    )

    assert response.status_code == 403
    assert "not yet approved" in response.json()["detail"].lower()


def test_owner_can_add_product_once_shop_approved(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    owner = _create_owner(test_db, username="approvedShopOwner2")
    _create_shop(test_db, owner, status="approved")
    headers = login(test_app, owner.username, "mys3cretp2ssw0rd")

    response = test_app.post(
        "/api/products",
        json=_sample_product_payload(),
        headers=headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Fainting Fancies"
    assert data["category"] == "Skiving Snackboxes"
    assert data["stock"] == 10


def test_owner_without_a_shop_cannot_add_product(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    owner = _create_owner(test_db, username="noShopOwner2")
    headers = login(test_app, owner.username, "mys3cretp2ssw0rd")

    response = test_app.post(
        "/api/products",
        json=_sample_product_payload(),
        headers=headers,
    )

    assert response.status_code == 404


def test_customer_cannot_add_product(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    _create_customer(test_db, username="shoppingCustomer2")
    headers = login(test_app, "shoppingCustomer2", "mys3cretp2ssw0rd")

    response = test_app.post(
        "/api/products",
        json=_sample_product_payload(),
        headers=headers,
    )

    # require_role("owner") blocks this before it even checks for a shop
    assert response.status_code == 403


# ---------------------------------------------------------------------
# Public product listing
# ---------------------------------------------------------------------

def test_products_list_excludes_unapproved_shops(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    pending_owner = _create_owner(test_db, username="stillPendingOwner2")
    _create_shop(test_db, pending_owner, status="pending", name="Pending Shop")

    approved_owner = _create_owner(test_db, username="visibleShopOwner2")
    approved_shop = _create_shop(test_db, approved_owner, status="approved", name="Visible Shop")
    headers = login(test_app, approved_owner.username, "mys3cretp2ssw0rd")
    test_app.post("/api/products", json=_sample_product_payload("Visible Product"), headers=headers)

    response = test_app.get("/api/products")

    assert response.status_code == 200
    names = [p["name"] for p in response.json()]
    assert "Visible Product" in names


def test_get_single_product(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    owner = _create_owner(test_db, username="singleProductOwner2")
    _create_shop(test_db, owner, status="approved")
    headers = login(test_app, owner.username, "mys3cretp2ssw0rd")

    create_response = test_app.post(
        "/api/products", json=_sample_product_payload("Nosebleed Nougat"), headers=headers
    )
    product_id = create_response.json()["id"]

    response = test_app.get(f"/api/products/{product_id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Nosebleed Nougat"


# ---------------------------------------------------------------------
# Ownership rules — only the owning shop owner, or admin, may edit/delete
# ---------------------------------------------------------------------

def test_owner_can_edit_own_product(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    owner = _create_owner(test_db, username="editOwnOwner2")
    _create_shop(test_db, owner, status="approved")
    headers = login(test_app, owner.username, "mys3cretp2ssw0rd")

    create_response = test_app.post(
        "/api/products", json=_sample_product_payload(), headers=headers
    )
    product_id = create_response.json()["id"]

    response = test_app.put(
        f"/api/products/{product_id}",
        json={"stock": 25},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["stock"] == 25


def test_owner_cannot_edit_other_owners_product(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    owner_a = _create_owner(test_db, username="ownerA2")
    _create_shop(test_db, owner_a, status="approved", name="Shop A")
    headers_a = login(test_app, owner_a.username, "mys3cretp2ssw0rd")
    create_response = test_app.post(
        "/api/products", json=_sample_product_payload("Owner A's Product"), headers=headers_a
    )
    product_id = create_response.json()["id"]

    owner_b = _create_owner(test_db, username="ownerB2")
    _create_shop(test_db, owner_b, status="approved", name="Shop B")
    headers_b = login(test_app, owner_b.username, "mys3cretp2ssw0rd")

    response = test_app.put(
        f"/api/products/{product_id}",
        json={"stock": 999},
        headers=headers_b,
    )

    assert response.status_code == 403


def test_owner_cannot_delete_other_owners_product(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    owner_a = _create_owner(test_db, username="ownerC2")
    _create_shop(test_db, owner_a, status="approved", name="Shop C")
    headers_a = login(test_app, owner_a.username, "mys3cretp2ssw0rd")
    create_response = test_app.post(
        "/api/products", json=_sample_product_payload("Owner C's Product"), headers=headers_a
    )
    product_id = create_response.json()["id"]

    owner_b = _create_owner(test_db, username="ownerD2")
    _create_shop(test_db, owner_b, status="approved", name="Shop D")
    headers_b = login(test_app, owner_b.username, "mys3cretp2ssw0rd")

    response = test_app.delete(f"/api/products/{product_id}", headers=headers_b)

    assert response.status_code == 403


def test_admin_can_edit_any_product(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    owner = _create_owner(test_db, username="adminEditTargetOwner2")
    _create_shop(test_db, owner, status="approved")
    owner_headers = login(test_app, owner.username, "mys3cretp2ssw0rd")
    create_response = test_app.post(
        "/api/products", json=_sample_product_payload(), headers=owner_headers
    )
    product_id = create_response.json()["id"]

    admin = _create_admin(test_db, username="adminEditor2")
    admin_headers = login(test_app, admin.username, "mys3cretp2ssw0rd")

    response = test_app.put(
        f"/api/products/{product_id}",
        json={"stock": 0},
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["stock"] == 0


def test_admin_can_delete_any_product(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    owner = _create_owner(test_db, username="adminDeleteTargetOwner2")
    _create_shop(test_db, owner, status="approved")
    owner_headers = login(test_app, owner.username, "mys3cretp2ssw0rd")
    create_response = test_app.post(
        "/api/products", json=_sample_product_payload("Bad Review Product"), headers=owner_headers
    )
    product_id = create_response.json()["id"]

    admin = _create_admin(test_db, username="adminDeleter2")
    admin_headers = login(test_app, admin.username, "mys3cretp2ssw0rd")

    response = test_app.delete(f"/api/products/{product_id}", headers=admin_headers)

    assert response.status_code == 204

    # Confirm it's actually gone
    get_response = test_app.get(f"/api/products/{product_id}")
    assert get_response.status_code == 404


def test_customer_cannot_edit_or_delete_product(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    owner = _create_owner(test_db, username="customerBlockedOwner2")
    _create_shop(test_db, owner, status="approved")
    owner_headers = login(test_app, owner.username, "mys3cretp2ssw0rd")
    create_response = test_app.post(
        "/api/products", json=_sample_product_payload(), headers=owner_headers
    )
    product_id = create_response.json()["id"]

    _create_customer(test_db, username="blockedCustomer2")
    customer_headers = login(test_app, "blockedCustomer2", "mys3cretp2ssw0rd")

    edit_response = test_app.put(
        f"/api/products/{product_id}", json={"stock": 1}, headers=customer_headers
    )
    delete_response = test_app.delete(f"/api/products/{product_id}", headers=customer_headers)

    # require_role("owner", "admin") blocks a plain customer from both
    assert edit_response.status_code == 403
    assert delete_response.status_code == 403