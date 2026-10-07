# models/shop.py

from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import BaseModel

class ShopModel(BaseModel):

    __tablename__ = "shops"

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # A rejected shop is declined before approval; suspended shops were previously approved.
    status = Column(
        Enum('pending', 'approved', 'suspended', 'rejected', name='shop_status'),
        default='pending'
    )

    owner = relationship("UserModel", backref="shops")

    @property
    def owner_username(self) -> str:
        return self.owner.username

    @property
    def is_authorized(self) -> bool:
        """A shop can only post products while status == 'approved'."""
        return self.status == 'approved'