# controllers/products.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.product import ProductModel
from models.shop import ShopModel
from models.user import UserModel
from serializers.product import ProductCreateSchema, ProductUpdateSchema, ProductSchema
from database import get_db
from dependencies.require_role import require_role

router = APIRouter()


def _get_my_shop_or_404(db: Session, user: UserModel) -> ShopModel:
    shop = db.query(ShopModel).filter(ShopModel.owner_id == user.id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="You don't have a shop yet")
    return shop


@router.post("/products", response_model=ProductSchema, status_code=201)
def create_product(
    product: ProductCreateSchema,
    db: Session = Depends(get_db),
    user: UserModel = Depends(require_role("owner")),
):
    shop = _get_my_shop_or_404(db, user)

    # US13 — a shop must be approved before it can post products
    if not shop.is_authorized:
        raise HTTPException(
            status_code=403,
            detail="Your shop is not yet approved by the admin"
        )

    new_product = ProductModel(shop_id=shop.id, **product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


@router.get("/products", response_model=list[ProductSchema])
def list_products(db: Session = Depends(get_db)):
    # Public route — only products from approved shops are shown
    return (
        db.query(ProductModel)
        .join(ShopModel)
        .filter(ShopModel.status == "approved")
        .all()
    )


@router.get("/products/{product_id}", response_model=ProductSchema)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def _authorize_product_edit(db: Session, product_id: int, user: UserModel) -> ProductModel:
    """
    Shared ownership check for update/delete:
    - Admin can touch any product
    - Owner can only touch products belonging to THEIR OWN shop
    - Everyone else gets 403
    """
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if user.role == "admin":
        return product

    if user.role == "owner":
        shop = db.query(ShopModel).filter(ShopModel.id == product.shop_id).first()
        if shop and shop.owner_id == user.id:
            return product

    raise HTTPException(status_code=403, detail="You do not have permission to modify this product")


@router.put("/products/{product_id}", response_model=ProductSchema)
def update_product(
    product_id: int,
    update: ProductUpdateSchema,
    db: Session = Depends(get_db),
    user: UserModel = Depends(require_role("owner", "admin")),
):
    product = _authorize_product_edit(db, product_id, user)

    for field, value in update.dict(exclude_unset=True).items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    user: UserModel = Depends(require_role("owner", "admin")),
):
    product = _authorize_product_edit(db, product_id, user)
    db.delete(product)
    db.commit()
    return None