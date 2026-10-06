# controllers/orders.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from decimal import Decimal

from models.order import OrderModel
from models.item import ItemModel
from models.product import ProductModel
from models.shop import ShopModel
from models.user import UserModel
from serializers.order import (
    AdminOrderSchema,
    OrderCreateSchema,
    OrderSchema,
    OrderStatusUpdateSchema,
    CouponValidateSchema,
)
from database import get_db
from dependencies.require_role import require_role

router = APIRouter()

# Rule 1 — a public, reusable coupon code
PUBLIC_COUPONS = {
    "DIAGONALLEY": 10,  # 10% off
}

# Rule 3 — automatic discount for a big order
BULK_ORDER_THRESHOLD = Decimal("20.00")
BULK_ORDER_DISCOUNT_PERCENT = 10

# Rule 2 — automatic discount on a customer's very first order
FIRST_ORDER_DISCOUNT_PERCENT = 15


def _best_discount_percent(db: Session, user: UserModel, coupon_code: str | None, total: Decimal) -> tuple[int, str | None]:
    """Returns (discount_percent, label_to_store_as_coupon_code)."""
    candidates = []  # list of (percent, label)

    if coupon_code:
        coupon_code = coupon_code.strip().upper()
        if coupon_code not in PUBLIC_COUPONS:
            raise HTTPException(status_code=400, detail="Invalid coupon code")
        candidates.append((PUBLIC_COUPONS[coupon_code], coupon_code))

    is_first_order = db.query(OrderModel).filter(OrderModel.user_id == user.id).count() == 0
    if is_first_order:
        candidates.append((FIRST_ORDER_DISCOUNT_PERCENT, "FIRST ORDER DISCOUNT"))

    if total >= BULK_ORDER_THRESHOLD:
        candidates.append((BULK_ORDER_DISCOUNT_PERCENT, "BULK ORDER DISCOUNT"))

    if not candidates:
        return 0, None

    # Pick whichever discount is biggest — no stacking
    return max(candidates, key=lambda c: c[0])


@router.post("/coupons/validate")
def validate_coupon(
    body: CouponValidateSchema,
    user: UserModel = Depends(require_role("user")),
):
    code = (body.coupon_code or "").strip().upper()
    if code not in PUBLIC_COUPONS:
        raise HTTPException(status_code=400, detail="Invalid coupon code")
    return {"coupon_code": code, "percent": PUBLIC_COUPONS[code], "valid": True}


@router.post("/orders", response_model=OrderSchema, status_code=201)
def checkout(
    order: OrderCreateSchema,
    db: Session = Depends(get_db),
    user: UserModel = Depends(require_role("user")),
):
    if not order.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    total = Decimal("0.00")
    order_items_to_create = []

    for cart_item in order.items:
        product = db.query(ProductModel).filter(ProductModel.id == cart_item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {cart_item.product_id} not found")

        if cart_item.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be at least 1")

        if cart_item.quantity > product.stock:
            raise HTTPException(
                status_code=400,
                detail=f"Only {product.stock} left of '{product.name}' — requested {cart_item.quantity}"
            )

        total += product.price_gbp * cart_item.quantity
        order_items_to_create.append((product, cart_item.quantity))

    discount_percent, applied_label = _best_discount_percent(db, user, order.coupon_code, total)
    if discount_percent:
        total = total - (total * Decimal(discount_percent) / Decimal(100))

    new_order = OrderModel(
        user_id=user.id,
        total_gbp=round(total, 2),
        coupon_code=applied_label,
        status="Owl Post Received",
    )
    db.add(new_order)
    db.flush()

    for product, quantity in order_items_to_create:
        db.add(ItemModel(
            order_id=new_order.id,
            product_id=product.id,
            quantity=quantity,
            price_at_purchase=product.price_gbp,
        ))
        product.stock -= quantity

    db.commit()
    db.refresh(new_order)
    return new_order


@router.get("/orders", response_model=list[OrderSchema])
def my_orders(
    db: Session = Depends(get_db),
    user: UserModel = Depends(require_role("user")),
):
    return db.query(OrderModel).filter(OrderModel.user_id == user.id).all()


@router.get("/orders/{order_id}", response_model=OrderSchema)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: UserModel = Depends(require_role("user", "admin")),
):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if user.role != "admin" and order.user_id != user.id:
        raise HTTPException(status_code=403, detail="This is not your order")

    return order


@router.get("/shops/mine/orders", response_model=list[OrderSchema])
def my_shop_orders(
    db: Session = Depends(get_db),
    user: UserModel = Depends(require_role("owner")),
):
    shop = db.query(ShopModel).filter(ShopModel.owner_id == user.id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="You don't have a shop yet")

    return (
        db.query(OrderModel)
        .join(ItemModel, ItemModel.order_id == OrderModel.id)
        .join(ProductModel, ProductModel.id == ItemModel.product_id)
        .filter(ProductModel.shop_id == shop.id)
        .distinct()
        .all()
    )


@router.get("/admin/orders", response_model=list[AdminOrderSchema])
def all_orders(
    db: Session = Depends(get_db),
    admin: UserModel = Depends(require_role("admin")),
):
    return db.query(OrderModel).options(joinedload(OrderModel.user)).all()


@router.put("/orders/{order_id}/status", response_model=OrderSchema)
def update_order_status(
    order_id: int,
    update: OrderStatusUpdateSchema,
    db: Session = Depends(get_db),
    user: UserModel = Depends(require_role("owner", "admin")),
):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if user.role == "owner":
        shop = db.query(ShopModel).filter(ShopModel.owner_id == user.id).first()
        owns_item_in_order = (
            db.query(ItemModel)
            .join(ProductModel, ProductModel.id == ItemModel.product_id)
            .filter(ItemModel.order_id == order_id, ProductModel.shop_id == shop.id)
            .first()
        )
        if not owns_item_in_order:
            raise HTTPException(status_code=403, detail="This order has none of your products")

    order.status = update.status
    db.commit()
    db.refresh(order)
    return order
@router.get("/shops/mine/stats")
def shop_sales_stats(
    db: Session = Depends(get_db),
    user: UserModel = Depends(require_role("owner")),
):
    shop = db.query(ShopModel).filter(ShopModel.owner_id == user.id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="You don't have a shop yet")
 
    results = (
        db.query(ProductModel.name, func.sum(ItemModel.quantity).label("units_sold"))
        .join(ItemModel, ItemModel.product_id == ProductModel.id)
        .filter(ProductModel.shop_id == shop.id)
        .group_by(ProductModel.name)
        .all()
    )
    return [{"name": name, "units_sold": int(units_sold)} for name, units_sold in results]
 