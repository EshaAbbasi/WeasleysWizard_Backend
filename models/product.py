# models/product.py

from sqlalchemy import Column, Integer, String, Numeric, Text, ForeignKey, Boolean, JSON, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel

PRODUCT_CATEGORIES = (
    "Trunk Station",
    "Wands",
    "Robes & Clothing",
    "Gifts",
    "Home and Accessories",
)

class ProductModel(BaseModel):

    __tablename__ = "products"

    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(Enum(*PRODUCT_CATEGORIES, name="product_category"), nullable=False)
    description = Column(Text, nullable=True)
    price_gbp = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0)
    image_urls = Column(JSON, default=list)
    is_banned_at_hogwarts = Column(Boolean, default=False)

    shop = relationship("ShopModel", backref="products")