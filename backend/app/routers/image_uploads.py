from fastapi import APIRouter, Depends, File, UploadFile

from app.core.deps import get_current_user
from app.core.oss import OssConfigError, upload_image_bytes
from app.models import User
from app.schemas.response import Response, fail, success

router = APIRouter()


@router.post("/upload", response_model=Response)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    try:
        content = await file.read()
        uploaded = await upload_image_bytes(
            user_id=current_user.id,
            content=content,
            content_type=file.content_type or "",
        )
    except (ValueError, OssConfigError) as e:
        return fail(str(e))
    except Exception:
        return fail("图片上传失败")
    finally:
        await file.close()

    return success(
        {
            "url": uploaded.url,
            "object_key": uploaded.object_key,
            "content_type": uploaded.content_type,
            "size": uploaded.size,
        }
    )
