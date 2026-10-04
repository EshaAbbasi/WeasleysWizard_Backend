# tests/test_items.py
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.user import UserModel
from models.shop import ShopModel
from models.product import ProductModel
from models.order import OrderModel
from models.item import ItemModel
from tests.lib import login


def _create_user(test_db: Session, username, role):
    user = UserModel(username=username, email=f"{username}@example.com", role=role)
    user.set_password("mys3cretp2ssw0rd")
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


def _create_shop(test_db: Session, owner, name="Item Test Shop"):
    shop = ShopModel(owner_id=owner.id, name=name, description="A shop", status="approved")
    test_db.add(shop)
    test_db.commit()
    test_db.refresh(shop)
    return shop


def _create_product(test_db: Session, shop, name="Extendable Ears", price="4.50", stock=20):
    product = ProductModel(
        shop_id=shop.id,
        name=name,
        category="Spy Gear",
        description="Hear what you shouldn't.",
        price_gbp=price,
        stock=stock,
        image_urls=[],
        is_banned_at_hogwarts=False,
    )
    test_db.add(product)
    test_db.commit()
    test_db.refresh(product)
    return product


def test_item_created_at_db_level_links_order_and_product(
    test_db: Session,
):
    owner = _create_user(test_db, "itemModelOwner", "owner")
    shop = _create_shop(test_db, owner)
    product = _create_product(test_db, shop)

    customer = _create_user(test_db, "itemModelCustomer", "user")

    order = OrderModel(user_id=customer.id, total_gbp="9.00", status="Owl Post Received")
    test_db.add(order)
    test_db.flush()

    item = ItemModel(
        order_id=order.id,
        product_id=product.id,
        quantity=2,
        price_at_purchase=product.price_gbp,
    )
    test_db.add(item)
    test_db.commit()
    test_db.refresh(item)

    assert item.order_id == order.id
    assert item.product_id == product.id
    assert item.quantity == 2
    assert float(item.price_at_purchase) == 4.50

    # Relationship access both ways
    assert item.order.id == order.id
    assert item.product.id == product.id
    assert order.items[0].id == item.id


def test_items_appear_nested_inside_order_response_via_api(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    owner = _create_user(test_db, "itemApiOwner", "owner")
    shop = _create_shop(test_db, owner, name="Item API Shop")
    product = _create_product(test_db, shop, name="Decoy Detonator", price="2.00", stock=15)

    customer = _create_user(test_db, "itemApiCustomer", "user")
    headers = login(test_app, customer.username, "mys3cretp2ssw0rd")

    response = test_app.post(
        "/api/orders",
        json={"items": [{"product_id": product.id, "quantity": 3}]},
        headers=headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["product_id"] == product.id
    assert data["items"][0]["quantity"] == 3
    assert float(data["items"][0]["price_at_purchase"]) == 2.00


def test_price_at_purchase_stays_locked_even_if_product_price_changes_later(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    owner = _create_user(test_db, "itemLockOwner", "owner")
    shop = _create_shop(test_db, owner, name="Item Lock Shop")
    product = _create_product(test_db, shop, name="Love Potion", price="5.00", stock=10)

    customer = _create_user(test_db, "itemLockCustomer", "user")
    headers = login(test_app, customer.username, "mys3cretp2ssw0rd")

    order_response = test_app.post(
        "/api/orders",
        json={"items": [{"product_id": product.id, "quantity": 1}]},
        headers=headers,
    )
    locked_price = order_response.json()["items"][0]["price_at_purchase"]
    assert float(locked_price) == 5.00

    # Shop owner raises the price afterward
    owner_headers = login(test_app, owner.username, "mys3cretp2ssw0rd")
    test_app.put(
        f"/api/products/{product.id}",
        json={"price_gbp": "9.99"},
        headers=owner_headers,
    )

    # The already-placed order's item must still show the ORIGINAL price
    order_check = test_app.get(f"/api/orders/{order_response.json()['id']}", headers=headers)
    assert float(order_check.json()["items"][0]["price_at_purchase"]) == 5.00


def test_no_direct_item_routes_exist(
    test_app: TestClient,
    test_db: Session,
    override_get_db,
):
    # Confirms the deliberate design choice: no standalone /items endpoints.
    # A 404 here means FastAPI has no matching route at all (correct);
    # anything else would mean an unintended route was added.
    response = test_app.get("/api/items")
    assert response.status_code == 404

    response = test_app.post("/api/items", json={})
    assert response.status_code == 404