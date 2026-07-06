import uuid

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.json_utils import dump_json_or_none
from app.core.oss import OssConfigError, upload_image_bytes
from app.models import ImageTask, User
from app.schemas.response import Response, fail, success

router = APIRouter()


@router.post("/upload", response_model=Response)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        content = await file.read()
        uploaded = await upload_image_bytes(
            user_id=current_user.id,
            content=content,
            content_type=file.content_type or "",
        )
        title = (file.filename or "用户上传图片").strip()[:100]
        task = ImageTask(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            type_id="upload",
            title=title or "用户上传图片",
            sort_order=0,
            prompt="用户上传图片",
            size="upload",
            status="done",
            result_url=uploaded.url,
            progress=100,
            provider="upload",
            provider_task_id=uploaded.object_key,
            credit_cost=0,
            prompt_snapshot_json=None,
            settings_snapshot_json=dump_json_or_none(
                {
                    "source": "upload",
                    "object_key": uploaded.object_key,
                    "content_type": uploaded.content_type,
                    "size": uploaded.size,
                }
            ),
        )
        db.add(task)
        await db.commit()
    except (ValueError, OssConfigError) as e:
        return fail(str(e))
    except Exception:
        await db.rollback()
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
