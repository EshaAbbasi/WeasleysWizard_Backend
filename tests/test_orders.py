# tests/test_orders.py

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


def _create_shop(test_db: Session, owner, name="Test Shop"):
    shop = ShopModel(owner_id=owner.id, name=name, description="A shop", status="approved")
    test_db.add(shop)
    test_db.commit()
    test_db.refresh(shop)
    return shop


def _create_product(test_db: Session, shop, name="Fainting Fancies", price="3.50", stock=10):
    product = ProductModel(
        shop_id=shop.id,
        name=name,
        category="Skiving Snackboxes",
        description="Turns you pale.",
        price_gbp=price,
        stock=stock,
        image_urls=[],
        is_banned_at_hogwarts=True,
    )
    test_db.add(product)
    test_db.commit()
    test_db.refresh(product)
    return product


def _setup_shop_with_product(test_db, owner_username="orderShopOwner", price="3.50", stock=10):
    owner = _create_user(test_db, owner_username, "owner")
    shop = _create_shop(test_db, owner, name=f"{owner_username} Shop")
    product = _create_product(test_db, shop, price=price, stock=stock)
    return owner, shop, product


# ---------------------------------------------------------------------
# Checkout + stock limits
# ---------------------------------------------------------------------

def test_customer_can_checkout(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    _owner, _shop, product = _setup_shop_with_product(test_db, "checkoutShopOwner")
    customer = _create_user(test_db, "checkoutCustomer", "user")
    headers = login(test_app, customer.username, "mys3cretp2ssw0rd")

    response = test_app.post(
        "/api/orders",
        json={"items": [{"product_id": product.id, "quantity": 2}]},
        headers=headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2
    assert float(data["total_gbp"]) == 7.00
    assert data["status"] == "Owl Post Received"


def test_checkout_reduces_stock(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    _owner, _shop, product = _setup_shop_with_product(test_db, "stockReduceOwner", stock=10)
    customer = _create_user(test_db, "stockReduceCustomer", "user")
    headers = login(test_app, customer.username, "mys3cretp2ssw0rd")

    test_app.post(
        "/api/orders",
        json={"items": [{"product_id": product.id, "quantity": 3}]},
        headers=headers,
    )

    product_response = test_app.get(f"/api/products/{product.id}")
    assert product_response.json()["stock"] == 7


def test_checkout_blocked_when_quantity_exceeds_stock(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    _owner, _shop, product = _setup_shop_with_product(test_db, "overstockOwner", stock=2)
    customer = _create_user(test_db, "overstockCustomer", "user")
    headers = login(test_app, customer.username, "mys3cretp2ssw0rd")

    response = test_app.post(
        "/api/orders",
        json={"items": [{"product_id": product.id, "quantity": 5}]},
        headers=headers,
    )

    assert response.status_code == 400

    # Stock must be unchanged since the order was rejected
    product_response = test_app.get(f"/api/products/{product.id}")
    assert product_response.json()["stock"] == 2


def test_checkout_fails_with_empty_cart(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    customer = _create_user(test_db, "emptyCartCustomer", "user")
    headers = login(test_app, customer.username, "mys3cretp2ssw0rd")

    response = test_app.post("/api/orders", json={"items": []}, headers=headers)

    assert response.status_code == 400


def test_checkout_fails_for_nonexistent_product(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    customer = _create_user(test_db, "badProductCustomer", "user")
    headers = login(test_app, customer.username, "mys3cretp2ssw0rd")

    response = test_app.post(
        "/api/orders",
        json={"items": [{"product_id": 999999, "quantity": 1}]},
        headers=headers,
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------
# Coupons
# ---------------------------------------------------------------------

def test_checkout_applies_valid_coupon(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    _owner, _shop, product = _setup_shop_with_product(
        test_db, "couponOwner", price="10.00", stock=10
    )
    customer = _create_user(test_db, "couponCustomer", "user")
    headers = login(test_app, customer.username, "mys3cretp2ssw0rd")

    response = test_app.post(
        "/api/orders",
        json={
            "items": [{"product_id": product.id, "quantity": 1}],
            "coupon_code": "DIAGONALLEY",
        },
        headers=headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["coupon_code"] == "DIAGONALLEY"
    assert float(data["total_gbp"]) == 9.00  # 10% off 10.00


def test_checkout_rejects_invalid_coupon(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    _owner, _shop, product = _setup_shop_with_product(test_db, "badCouponOwner")
    customer = _create_user(test_db, "badCouponCustomer", "user")
    headers = login(test_app, customer.username, "mys3cretp2ssw0rd")

    response = test_app.post(
        "/api/orders",
        json={
            "items": [{"product_id": product.id, "quantity": 1}],
            "coupon_code": "NOTREAL",
        },
        headers=headers,
    )

    assert response.status_code == 400


# ---------------------------------------------------------------------
# Visibility: customer / shop owner / admin
# ---------------------------------------------------------------------

def test_customer_only_sees_own_orders(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    _owner, _shop, product = _setup_shop_with_product(test_db, "visOwner1")

    customer_a = _create_user(test_db, "visCustomerA", "user")
    headers_a = login(test_app, customer_a.username, "mys3cretp2ssw0rd")
    test_app.post(
        "/api/orders", json={"items": [{"product_id": product.id, "quantity": 1}]}, headers=headers_a
    )

    customer_b = _create_user(test_db, "visCustomerB", "user")
    headers_b = login(test_app, customer_b.username, "mys3cretp2ssw0rd")

    response = test_app.get("/api/orders", headers=headers_b)

    assert response.status_code == 200
    assert response.json() == []  # customer B has no orders of their own


def test_shop_owner_sees_orders_containing_their_products(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    owner, _shop, product = _setup_shop_with_product(test_db, "shopOrdersOwner")
    owner_headers = login(test_app, owner.username, "mys3cretp2ssw0rd")

    customer = _create_user(test_db, "shopOrdersCustomer", "user")
    customer_headers = login(test_app, customer.username, "mys3cretp2ssw0rd")
    test_app.post(
        "/api/orders",
        json={"items": [{"product_id": product.id, "quantity": 1}]},
        headers=customer_headers,
    )

    response = test_app.get("/api/shops/mine/orders", headers=owner_headers)

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_admin_sees_all_orders(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    _owner, _shop, product = _setup_shop_with_product(test_db, "adminOrdersOwner")
    customer = _create_user(test_db, "adminOrdersCustomer", "user")
    customer_headers = login(test_app, customer.username, "mys3cretp2ssw0rd")
    test_app.post(
        "/api/orders",
        json={"items": [{"product_id": product.id, "quantity": 1}]},
        headers=customer_headers,
    )

    admin = _create_user(test_db, "adminOrdersAdmin", "admin")
    admin_headers = login(test_app, admin.username, "mys3cretp2ssw0rd")

    response = test_app.get("/api/admin/orders", headers=admin_headers)

    assert response.status_code == 200
    assert len(response.json()) >= 1


# ---------------------------------------------------------------------
# Order status updates
# ---------------------------------------------------------------------

def test_owner_can_update_status_of_order_with_their_product(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    owner, _shop, product = _setup_shop_with_product(test_db, "statusOwner1")
    owner_headers = login(test_app, owner.username, "mys3cretp2ssw0rd")

    customer = _create_user(test_db, "statusCustomer1", "user")
    customer_headers = login(test_app, customer.username, "mys3cretp2ssw0rd")
    order_response = test_app.post(
        "/api/orders",
        json={"items": [{"product_id": product.id, "quantity": 1}]},
        headers=customer_headers,
    )
    order_id = order_response.json()["id"]

    response = test_app.put(
        f"/api/orders/{order_id}/status",
        json={"status": "In Transit via Floo Network"},
        headers=owner_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "In Transit via Floo Network"


def test_owner_cannot_update_status_of_unrelated_order(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    _owner_a, _shop_a, product_a = _setup_shop_with_product(test_db, "statusOwnerA")
    owner_b, _shop_b, _product_b = _setup_shop_with_product(test_db, "statusOwnerB")
    owner_b_headers = login(test_app, owner_b.username, "mys3cretp2ssw0rd")

    customer = _create_user(test_db, "statusCustomer2", "user")
    customer_headers = login(test_app, customer.username, "mys3cretp2ssw0rd")
    order_response = test_app.post(
        "/api/orders",
        json={"items": [{"product_id": product_a.id, "quantity": 1}]},
        headers=customer_headers,
    )
    order_id = order_response.json()["id"]

    # Owner B's shop has nothing to do with this order
    response = test_app.put(
        f"/api/orders/{order_id}/status",
        json={"status": "Delivered"},
        headers=owner_b_headers,
    )

    assert response.status_code == 403


def test_customer_cannot_view_others_order_by_id(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    _owner, _shop, product = _setup_shop_with_product(test_db, "privateOrderOwner")

    customer_a = _create_user(test_db, "privateOrderCustomerA", "user")
    headers_a = login(test_app, customer_a.username, "mys3cretp2ssw0rd")
    order_response = test_app.post(
        "/api/orders", json={"items": [{"product_id": product.id, "quantity": 1}]}, headers=headers_a
    )
    order_id = order_response.json()["id"]

    customer_b = _create_user(test_db, "privateOrderCustomerB", "user")
    headers_b = login(test_app, customer_b.username, "mys3cretp2ssw0rd")

    response = test_app.get(f"/api/orders/{order_id}", headers=headers_b)

    assert response.status_code == 403