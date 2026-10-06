# serializers/order.py

from pydantic import BaseModel
from typing import List, Optional, Literal
from decimal import Decimal
from serializers.item import ItemInputSchema, ItemSchema

# What the customer sends to checkout
class OrderCreateSchema(BaseModel):
    items: List[ItemInputSchema]
    coupon_code: Optional[str] = None

class OrderStatusUpdateSchema(BaseModel):
    status: Literal['Owl Post Received', 'In Transit via Floo Network', 'Delivered']

# What gets returned back
class CouponValidateSchema(BaseModel):
    coupon_code: str

class OrderSchema(BaseModel):
    id: int
    user_id: int
    total_gbp: Decimal
    coupon_code: Optional[str] = None
    status: str
    payment_method: str = "Cash on Delivery"
    items: List[ItemSchema] = []

    class Config:
        orm_mode = True

class AdminOrderSchema(OrderSchema):
    customer_username: str