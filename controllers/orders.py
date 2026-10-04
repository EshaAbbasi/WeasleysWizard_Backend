# controllers/orders.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal

from models.order import OrderModel
from models.item import ItemModel
from models.product import ProductModel
from models.shop import ShopModel
from models.user import UserModel
from serializers.order import OrderCreateSchema, OrderSchema, OrderStatusUpdateSchema
from database import get_db
from dependencies.require_role import require_role

router = APIRouter()

# Coupons — hardcoded for MVP, as discussed (no coupons table yet)
VALID_COUPONS = {
    "DIAGONALLEY": 10,        # 10% off
    "WEASLEYISOURKING": 15,   # 15% off
}


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

    # Step 1: validate every product and stock BEFORE creating anything
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

        line_total = product.price_gbp * cart_item.quantity
        total += line_total

        order_items_to_create.append((product, cart_item.quantity))

    # Step 2: apply coupon, if provided
    coupon_code = None
    if order.coupon_code:
        if order.coupon_code not in VALID_COUPONS:
            raise HTTPException(status_code=400, detail="Invalid coupon code")
        discount_percent = VALID_COUPONS[order.coupon_code]
        total = total - (total * Decimal(discount_percent) / Decimal(100))
        coupon_code = order.coupon_code

    # Step 3: create the order
    new_order = OrderModel(
        user_id=user.id,
        total_gbp=round(total, 2),
        coupon_code=coupon_code,
        status="Owl Post Received",
    )
    db.add(new_order)
    db.flush()  # gets new_order.id without a full commit yet

    # Step 4: create each item, and decrement stock
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

    # Orders that contain at least one of this shop's products
    return (
        db.query(OrderModel)
        .join(ItemModel, ItemModel.order_id == OrderModel.id)
        .join(ProductModel, ProductModel.id == ItemModel.product_id)
        .filter(ProductModel.shop_id == shop.id)
        .distinct()
        .all()
    )


@router.get("/admin/orders", response_model=list[OrderSchema])
def all_orders(
    db: Session = Depends(get_db),
    admin: UserModel = Depends(require_role("admin")),
):
    return db.query(OrderModel).all()


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
        # Confirm this order actually contains one of the owner's products
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