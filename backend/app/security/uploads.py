"""
File upload validation: content-type allowlist + size limit, and a
collision-resistant filename so user input never controls the path written
to disk (prevents path traversal / overwrite attacks).
"""
import os
import uuid

from fastapi import HTTPException, UploadFile

from app.config import get_settings

settings = get_settings()


def _extension_for(content_type: str) -> str:
    return {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "video/mp4": ".mp4",
        "video/webm": ".webm",
        "video/quicktime": ".mov",
    }.get(content_type, "")


async def save_upload(file: UploadFile, subdir: str, kind: str = "image") -> str:
    allowed = settings.allowed_image_types if kind == "image" else settings.allowed_video_types
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File too large (max {settings.MAX_UPLOAD_SIZE_MB}MB)")
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    ext = _extension_for(file.content_type)
    filename = f"{uuid.uuid4().hex}{ext}"
    target_dir = os.path.join(settings.UPLOAD_DIR, subdir)
    os.makedirs(target_dir, exist_ok=True)
    path = os.path.join(target_dir, filename)
    with open(path, "wb") as f:
        f.write(contents)

    return f"/{path}"
