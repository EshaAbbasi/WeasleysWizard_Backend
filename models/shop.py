# models/shop.py

from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import BaseModel

class ShopModel(BaseModel):

    __tablename__ = "shops"

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Single source of truth for approval state — "pending" until an
    # admin approves it, "suspended" if an admin removes it later.
    status = Column(
        Enum('pending', 'approved', 'suspended', name='shop_status'),
        default='pending'
    )

    owner = relationship("UserModel", backref="shops")

    @property
    def is_authorized(self) -> bool:
        """A shop can only post products while status == 'approved'."""
        return self.status == 'approved'