# controllers/reviews.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.review import ReviewModel
from models.product import ProductModel
from models.user import UserModel
from serializers.review import ReviewCreateSchema, ReviewUpdateSchema, ReviewSchema
from database import get_db
from dependencies.require_role import require_role
from dependencies.get_current_user import get_current_user

router = APIRouter()


@router.post("/reviews", response_model=ReviewSchema, status_code=201)
def create_or_update_review(
    review: ReviewCreateSchema,
    db: Session = Depends(get_db),
    user: UserModel = Depends(require_role("user")),
):
    product = db.query(ProductModel).filter(ProductModel.id == review.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Upsert: one review row per (user, product) — prevents duplicate
    # favorites/reviews on the same product, as discussed earlier.
    existing = (
        db.query(ReviewModel)
        .filter(ReviewModel.user_id == user.id, ReviewModel.product_id == review.product_id)
        .first()
    )

    if existing:
        existing.rating = review.rating
        existing.comment = review.comment
        existing.image_urls = review.image_urls
        existing.is_favorite = review.is_favorite
        db.commit()
        db.refresh(existing)
        return existing

    new_review = ReviewModel(
        user_id=user.id,
        product_id=review.product_id,
        rating=review.rating,
        comment=review.comment,
        image_urls=review.image_urls,
        is_favorite=review.is_favorite,
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review


@router.get("/reviews/{product_id}", response_model=list[ReviewSchema])
def list_reviews_for_product(product_id: int, db: Session = Depends(get_db)):
    # Public — anyone can read reviews on a product page
    return db.query(ReviewModel).filter(ReviewModel.product_id == product_id).all()


@router.get("/favorites", response_model=list[ReviewSchema])
def my_favorites(
    db: Session = Depends(get_db),
    user: UserModel = Depends(require_role("user")),
):
    return (
        db.query(ReviewModel)
        .filter(ReviewModel.user_id == user.id, ReviewModel.is_favorite == True)  # noqa: E712
        .all()
    )


@router.get("/admin/reviews", response_model=list[ReviewSchema])
def all_reviews(
    db: Session = Depends(get_db),
    admin: UserModel = Depends(require_role("admin")),
):
    # Admin oversight — e.g. spotting a product with a pattern of bad reviews
    return db.query(ReviewModel).all()


def _get_own_review_or_admin(db: Session, review_id: int, user: UserModel) -> ReviewModel:
    review = db.query(ReviewModel).filter(ReviewModel.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if user.role != "admin" and review.user_id != user.id:
        raise HTTPException(status_code=403, detail="You can only modify your own review")

    return review


@router.put("/reviews/{review_id}", response_model=ReviewSchema)
def update_review(
    review_id: int,
    update: ReviewUpdateSchema,
    db: Session = Depends(get_db),
    user: UserModel = Depends(get_current_user),
):
    review = _get_own_review_or_admin(db, review_id, user)

    for field, value in update.dict(exclude_unset=True).items():
        setattr(review, field, value)

    db.commit()
    db.refresh(review)
    return review


@router.delete("/reviews/{review_id}", status_code=204)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    user: UserModel = Depends(get_current_user),
):
    review = _get_own_review_or_admin(db, review_id, user)
    db.delete(review)
    db.commit()
    return None