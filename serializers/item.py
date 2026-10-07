# serializers/item.py

from pydantic import BaseModel
from decimal import Decimal

# What the customer sends for EACH product in their cart at checkout
class ItemInputSchema(BaseModel):
    product_id: int
    quantity: int

# What gets returned back inside an order's response
class ItemSchema(BaseModel):
    id: int
    product_id: int
    quantity: int
    price_at_purchase: Decimal

    class Config:
        from_attributes = True