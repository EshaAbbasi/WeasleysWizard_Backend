import os
from dotenv import load_dotenv

load_dotenv()

from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models.base import Base
from models.user import UserModel
from models.shop import ShopModel
from models.product import ProductModel
from models.order import OrderModel
from models.item import ItemModel
from models.review import ReviewModel

from fastapi import FastAPI

# Controllers
from controllers.users import router as UsersRouter
from controllers.shops import router as ShopsRouter
from controllers.products import router as ProductsRouter
from controllers.orders import router as OrdersRouter
from controllers.reviews import router as ReviewsRouter
from controllers.uploads import router as UploadsRouter

Base.metadata.create_all(bind=engine)

app = FastAPI()

cors_from_env = os.getenv("CORS_ORIGINS") or os.getenv("CORS_ORIGIN") or ""
origins = [
    origin.strip()
    for origin in cors_from_env.split(",")
    if origin.strip()
]
for local in ("http://localhost:5173", "http://127.0.0.1:5173"):
    if local not in origins:
        origins.append(local)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.(vercel\.app|onrender\.com)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(UsersRouter, prefix='/api')
app.include_router(ShopsRouter, prefix='/api')
app.include_router(ProductsRouter, prefix='/api')
app.include_router(OrdersRouter, prefix='/api')
app.include_router(ReviewsRouter, prefix='/api')
app.include_router(UploadsRouter, prefix='/api')

@app.get('/health')
def health_check():
  return {'message': 'Api is running'}