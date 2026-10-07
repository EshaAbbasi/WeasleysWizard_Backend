# serializers/review.py

from pydantic import BaseModel
from typing import Optional, List

class ReviewCreateSchema(BaseModel):
    product_id: int
    rating: Optional[int] = None          # 1-5, optional so a pure favorite can skip it
    comment: Optional[str] = None
    image_urls: List[str] = []
    is_favorite: bool = False

class ReviewUpdateSchema(BaseModel):
    rating: Optional[int] = None
    comment: Optional[str] = None
    image_urls: Optional[List[str]] = None
    is_favorite: Optional[bool] = None

class ReviewSchema(BaseModel):
    id: int
    user_id: int
    product_id: int
    rating: Optional[int] = None
    comment: Optional[str] = None
    image_urls: List[str] = []
    is_favorite: bool

    class Config:
       from_attributes=True