import os
from fastapi.middleware.cors import CORSMiddleware
from database import engine 
from models.base import Base
from models.user import UserModel 
from models.shop import ShopModel
from models.product import ProductModel
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI

# Controllers
from controllers.users import router as UsersRouter
from controllers.shops import router as ShopsRouter
from controllers.products import router as ProductsRouter
# Create all tables that don't exist yet
Base.metadata.create_all(bind=engine)


app = FastAPI()

# ✅ Allow your React dev server(s) to call the API
origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,     # Which sites can call this API
    allow_methods=["*"],       # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],       # Allow all headers (e.g., Content-Type, Authorization)
)

app.include_router(UsersRouter, prefix='/api')
app.include_router(ShopsRouter, prefix='/api') 
app.include_router(ProductsRouter, prefix='/api') 

@app.get('/health')
def health_check():
  return {'message': 'Api is running'}