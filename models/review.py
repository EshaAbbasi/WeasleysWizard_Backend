# models/review.py

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from .base import BaseModel

class ReviewModel(BaseModel):

    __tablename__ = "reviews"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    rating = Column(Integer, nullable=True)        # 1-5, nullable so a pure "favorite" can skip it
    comment = Column(Text, nullable=True)
    image_urls = Column(JSON, default=list)
    is_favorite = Column(Boolean, default=False)

    user = relationship("UserModel", backref="reviews")
    product = relationship("ProductModel", backref="reviews")