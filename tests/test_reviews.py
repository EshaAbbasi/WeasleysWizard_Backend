# tests/test_reviews.py

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.user import UserModel
from models.shop import ShopModel
from models.product import ProductModel
from tests.lib import login


def _create_user(test_db: Session, username, role):
    user = UserModel(username=username, email=f"{username}@example.com", role=role)
    user.set_password("mys3cretp2ssw0rd")
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


def _create_shop(test_db: Session, owner, name="Review Test Shop"):
    shop = ShopModel(owner_id=owner.id, name=name, description="A shop", status="approved")
    test_db.add(shop)
    test_db.commit()
    test_db.refresh(shop)
    return shop


def _create_product(test_db: Session, shop, name="Puking Pastilles", price="2.50", stock=15):
    product = ProductModel(
        shop_id=shop.id,
        name=name,
        category="Skiving Snackboxes",
        description="Two halves, two effects.",
        price_gbp=price,
        stock=stock,
        image_urls=[],
        is_banned_at_hogwarts=True,
    )
    test_db.add(product)
    test_db.commit()
    test_db.refresh(product)
    return product


def _setup_product(test_db, owner_username="reviewShopOwner"):
    owner = _create_user(test_db, owner_username, "owner")
    shop = _create_shop(test_db, owner, name=f"{owner_username} Shop")
    product = _create_product(test_db, shop)
    return owner, shop, product


# ---------------------------------------------------------------------
# Creating reviews / favorites
# ---------------------------------------------------------------------

def test_customer_can_create_review_with_rating_and_comment(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    _owner, _shop, product = _setup_product(test_db, "reviewOwner1")
    customer = _create_user(test_db, "reviewCustomer1", "user")
    headers = login(test_app, customer.username, "mys3cretp2ssw0rd")

    response = test_app.post(
        "/api/reviews",
        json={
            "product_id": product.id,
            "rating": 5,
            "comment": "Made my brother faint for a whole afternoon!",
            "image_urls": [],
            "is_favorite": False,
        },
        headers=headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["rating"] == 5
    assert data["comment"] == "Made my brother faint for a whole afternoon!"


def test_customer_can_favorite_without_rating_or_comment(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    _owner, _shop, product = _setup_product(test_db, "reviewOwner2")
    customer = _create_user(test_db, "reviewCustomer2", "user")
    headers = login(test_app, customer.username, "mys3cretp2ssw0rd")

    response = test_app.post(
        "/api/reviews",
        json={"product_id": product.id, "is_favorite": True},
        headers=headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["is_favorite"] is True
    assert data["rating"] is None
    assert data["comment"] is None


def test_second_review_on_same_product_updates_instead_of_duplicating(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    _owner, _shop, product = _setup_product(test_db, "reviewOwner3")
    customer = _create_user(test_db, "reviewCustomer3", "user")
    headers = login(test_app, customer.username, "mys3cretp2ssw0rd")

    first = test_app.post(
        "/api/reviews",
        json={"product_id": product.id, "rating": 2, "comment": "Meh"},
        headers=headers,
    )
    first_id = first.json()["id"]

    second = test_app.post(
        "/api/reviews",
        json={"product_id": product.id, "rating": 5, "comment": "Changed my mind, love it!"},
        headers=headers,
    )

    assert second.status_code == 201
    assert second.json()["id"] == first_id  # same row, updated — no duplicate
    assert second.json()["rating"] == 5

    all_reviews = test_app.get(f"/api/reviews/{product.id}")
    assert len(all_reviews.json()) == 1  # confirms no duplicate row was created


def test_review_requires_existing_product(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    customer = _create_user(test_db, "reviewCustomer4", "user")
    headers = login(test_app, customer.username, "mys3cretp2ssw0rd")

    response = test_app.post(
        "/api/reviews",
        json={"product_id": 999999, "rating": 4},
        headers=headers,
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------
# Public visibility
# ---------------------------------------------------------------------

def test_reviews_are_publicly_visible(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    _owner, _shop, product = _setup_product(test_db, "reviewOwner5")
    customer = _create_user(test_db, "reviewCustomer5", "user")
    headers = login(test_app, customer.username, "mys3cretp2ssw0rd")
    test_app.post(
        "/api/reviews",
        json={"product_id": product.id, "rating": 4, "comment": "Pretty good"},
        headers=headers,
    )

    # No auth header at all
    response = test_app.get(f"/api/reviews/{product.id}")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["comment"] == "Pretty good"


# ---------------------------------------------------------------------
# Favorites list
# ---------------------------------------------------------------------

def test_favorites_list_only_shows_own_favorites(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    _owner, _shop, product_a = _setup_product(test_db, "favOwnerA")
    _owner_b, shop_b, _ = (None, None, None)
    product_b = _create_product(
        test_db,
        _create_shop(test_db, _create_user(test_db, "favOwnerB", "owner"), name="Fav Shop B"),
        name="Second Product",
    )

    customer_a = _create_user(test_db, "favCustomerA", "user")
    headers_a = login(test_app, customer_a.username, "mys3cretp2ssw0rd")
    test_app.post("/api/reviews", json={"product_id": product_a.id, "is_favorite": True}, headers=headers_a)
    test_app.post("/api/reviews", json={"product_id": product_b.id, "is_favorite": False, "rating": 3}, headers=headers_a)

    customer_b = _create_user(test_db, "favCustomerB", "user")
    headers_b = login(test_app, customer_b.username, "mys3cretp2ssw0rd")
    test_app.post("/api/reviews", json={"product_id": product_b.id, "is_favorite": True}, headers=headers_b)

    response_a = test_app.get("/api/favorites", headers=headers_a)

    assert response_a.status_code == 200
    favorite_product_ids = [r["product_id"] for r in response_a.json()]
    assert product_a.id in favorite_product_ids
    assert product_b.id not in favorite_product_ids  # that one wasn't favorited by A


# ---------------------------------------------------------------------
# Ownership: edit/delete only your own review, admin can override
# ---------------------------------------------------------------------

def test_customer_can_edit_own_review(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    _owner, _shop, product = _setup_product(test_db, "reviewOwner6")
    customer = _create_user(test_db, "reviewCustomer6", "user")
    headers = login(test_app, customer.username, "mys3cretp2ssw0rd")
    create_response = test_app.post(
        "/api/reviews", json={"product_id": product.id, "rating": 3}, headers=headers
    )
    review_id = create_response.json()["id"]

    response = test_app.put(
        f"/api/reviews/{review_id}", json={"rating": 5}, headers=headers
    )

    assert response.status_code == 200
    assert response.json()["rating"] == 5


def test_customer_cannot_edit_other_customers_review(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    _owner, _shop, product = _setup_product(test_db, "reviewOwner7")

    customer_a = _create_user(test_db, "reviewCustomerA7", "user")
    headers_a = login(test_app, customer_a.username, "mys3cretp2ssw0rd")
    create_response = test_app.post(
        "/api/reviews", json={"product_id": product.id, "rating": 1}, headers=headers_a
    )
    review_id = create_response.json()["id"]

    customer_b = _create_user(test_db, "reviewCustomerB7", "user")
    headers_b = login(test_app, customer_b.username, "mys3cretp2ssw0rd")

    response = test_app.put(
        f"/api/reviews/{review_id}", json={"rating": 5}, headers=headers_b
    )

    assert response.status_code == 403


def test_customer_can_delete_own_review(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    _owner, _shop, product = _setup_product(test_db, "reviewOwner8")
    customer = _create_user(test_db, "reviewCustomer8", "user")
    headers = login(test_app, customer.username, "mys3cretp2ssw0rd")
    create_response = test_app.post(
        "/api/reviews", json={"product_id": product.id, "rating": 2}, headers=headers
    )
    review_id = create_response.json()["id"]

    response = test_app.delete(f"/api/reviews/{review_id}", headers=headers)

    assert response.status_code == 204

    all_reviews = test_app.get(f"/api/reviews/{product.id}")
    assert all_reviews.json() == []


def test_admin_can_delete_any_review(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    _owner, _shop, product = _setup_product(test_db, "reviewOwner9")
    customer = _create_user(test_db, "reviewCustomer9", "user")
    headers = login(test_app, customer.username, "mys3cretp2ssw0rd")
    create_response = test_app.post(
        "/api/reviews", json={"product_id": product.id, "rating": 1, "comment": "Terrible"}, headers=headers
    )
    review_id = create_response.json()["id"]

    admin = _create_user(test_db, "reviewAdmin9", "admin")
    admin_headers = login(test_app, admin.username, "mys3cretp2ssw0rd")

    response = test_app.delete(f"/api/reviews/{review_id}", headers=admin_headers)

    assert response.status_code == 204


def test_admin_can_see_all_reviews_platform_wide(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    _owner, _shop, product = _setup_product(test_db, "reviewOwner10")
    customer = _create_user(test_db, "reviewCustomer10", "user")
    headers = login(test_app, customer.username, "mys3cretp2ssw0rd")
    test_app.post(
        "/api/reviews", json={"product_id": product.id, "rating": 1}, headers=headers
    )

    admin = _create_user(test_db, "reviewAdmin10", "admin")
    admin_headers = login(test_app, admin.username, "mys3cretp2ssw0rd")

    response = test_app.get("/api/admin/reviews", headers=admin_headers)

    assert response.status_code == 200
    assert len(response.json()) >= 1