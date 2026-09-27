from fastapi import APIRouter, Depends, UploadFile, File

from app.auth.deps import get_current_user
from app.models.user import User
from app.security.uploads import save_upload

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.post("/image")
async def upload_image(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    url = await save_upload(file, subdir="posts", kind="image")
    return {"url": url}


@router.post("/video")
async def upload_video(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    url = await save_upload(file, subdir="reels", kind="video")
    return {"url": url}


@router.post("/avatar")
async def upload_avatar(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    url = await save_upload(file, subdir="avatars", kind="image")
    return {"url": url}
