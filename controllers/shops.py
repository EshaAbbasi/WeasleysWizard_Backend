# controllers/shops.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.shop import ShopModel
from models.user import UserModel
from serializers.shop import ShopCreateSchema, ShopSchema, ShopStatusUpdateSchema
from database import get_db
from dependencies.get_current_user import get_current_user
from dependencies.require_role import require_role

router = APIRouter()


@router.post("/shops", response_model=ShopSchema, status_code=201)
def create_shop(
    shop: ShopCreateSchema,
    db: Session = Depends(get_db),
    user: UserModel = Depends(require_role("owner")),
):
    # Keep it simple: one shop per owner for this project's scope
    existing = db.query(ShopModel).filter(ShopModel.owner_id == user.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="You already have a shop")

    new_shop = ShopModel(
        owner_id=user.id,
        name=shop.name,
        description=shop.description,
        status="pending",
    )
    db.add(new_shop)
    db.commit()
    db.refresh(new_shop)
    return new_shop


@router.get("/shops/mine", response_model=ShopSchema)
def get_my_shop(
    db: Session = Depends(get_db),
    user: UserModel = Depends(require_role("owner")),
):
    shop = db.query(ShopModel).filter(ShopModel.owner_id == user.id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="You don't have a shop yet")
    return shop


@router.get("/shops", response_model=list[ShopSchema])
def list_authorized_shops(db: Session = Depends(get_db)):
    # Public route — customers should only ever see approved shops
    return db.query(ShopModel).filter(ShopModel.status == "approved").all()


@router.get("/admin/shops", response_model=list[ShopSchema])
def list_all_shops(
    db: Session = Depends(get_db),
    admin: UserModel = Depends(require_role("admin")),
):
    # Admin sees everything, including pending and suspended
    return db.query(ShopModel).all()


@router.put("/admin/shops/{shop_id}/status", response_model=ShopSchema)
def update_shop_status(
    shop_id: int,
    update: ShopStatusUpdateSchema,
    db: Session = Depends(get_db),
    admin: UserModel = Depends(require_role("admin")),
):
    shop = db.query(ShopModel).filter(ShopModel.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    shop.status = update.status
    db.commit()
    db.refresh(shop)
    return shop