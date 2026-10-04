# models/item.py

from sqlalchemy import Column, Integer, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class ItemModel(BaseModel):

    __tablename__ = "items"

    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    price_at_purchase = Column(Numeric(10, 2), nullable=False)  # locks price even if product price changes later

    order = relationship("OrderModel", backref="items")
    product = relationship("ProductModel")