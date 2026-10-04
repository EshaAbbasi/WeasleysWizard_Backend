# models/order.py

from sqlalchemy import Column, Integer, Numeric, String, Enum, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class OrderModel(BaseModel):

    __tablename__ = "orders"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_gbp = Column(Numeric(10, 2), nullable=False)
    coupon_code = Column(String, nullable=True)
    status = Column(
        Enum(
            'Owl Post Received',
            'In Transit via Floo Network',
            'Delivered',
            name='order_status'
        ),
        default='Owl Post Received'
    )

    user = relationship("UserModel", backref="orders")