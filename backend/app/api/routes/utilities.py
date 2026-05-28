import io
import uuid

from fastapi import HTTPException, UploadFile
from PIL import Image

from app.config import settings


async def load_photo(photo: UploadFile) -> tuple[bytes, Image.Image, str]:

    # image validation
    if photo.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, and WebP files are accepted")
    
    contents = await photo.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large, max size is 10MB")
    
    image = Image.open(io.BytesIO(contents)).convert("RGB")
    if image.width < 50 or image.height < 50:
        raise HTTPException(status_code=400, detail="Image too small, min size is 50x50px")
    
    suffix_map = {"image/jpeg": ".jpeg", "image/png": ".png", "image/webp": ".webp"}
    suffix = suffix_map[photo.content_type]
    photo_filename = f"{uuid.uuid4()}{suffix}"
    photo_path = settings.media_dir / "uploads" / photo_filename
    photo_path.write_bytes(contents)
    photo_url = f"/media/uploads/{photo_filename}"

    return contents, image, photo_url