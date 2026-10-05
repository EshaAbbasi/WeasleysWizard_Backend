# controllers/uploads.py

import os
import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from models.user import UserModel
from dependencies.get_current_user import get_current_user

router = APIRouter()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)


@router.post("/upload-image")
def upload_image(
    file: UploadFile = File(...),
    user: UserModel = Depends(get_current_user),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    try:
        result = cloudinary.uploader.upload(file.file)
    except Exception as err:
        raise HTTPException(status_code=502, detail=f"Image upload failed: {str(err)}")

    return {"url": result["secure_url"]}