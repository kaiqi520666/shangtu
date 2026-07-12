import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.json_utils import dump_json_or_none
from app.core.oss import OssConfigError, UploadedFile, upload_audio_bytes, upload_video_bytes
from app.models import UserAudioAsset, VideoTask


@dataclass(slots=True)
class VideoUploadCreation:
    uploaded: UploadedFile | None
    error_message: str | None = None


@dataclass(slots=True)
class AudioUploadCreation:
    uploaded: UploadedFile | None
    asset_id: str | None = None
    error_message: str | None = None


async def create_uploaded_video(
    db: AsyncSession,
    *,
    user_id: int,
    content: bytes,
    content_type: str,
    filename: str | None,
) -> VideoUploadCreation:
    try:
        uploaded = await upload_video_bytes(
            user_id=user_id,
            content=content,
            content_type=content_type,
            source="video-uploads",
        )
        title = (filename or "用户上传视频").strip()[:100]
        task = VideoTask(
            id=str(uuid.uuid4()),
            user_id=user_id,
            scenario="upload",
            type_id="upload",
            title=title or "用户上传视频",
            sort_order=0,
            prompt="用户上传视频",
            input_mode="upload",
            input_images_json=None,
            input_video_url=uploaded.url,
            duration=0,
            resolution="upload",
            aspect_ratio="original",
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
    except (ValueError, OssConfigError) as exc:
        return VideoUploadCreation(None, str(exc))
    except Exception:
        await db.rollback()
        return VideoUploadCreation(None, "视频上传失败")
    return VideoUploadCreation(uploaded)


async def create_reference_audio(
    db: AsyncSession,
    *,
    user_id: int,
    content: bytes,
    content_type: str,
    filename: str | None,
) -> AudioUploadCreation:
    try:
        uploaded = await upload_audio_bytes(
            user_id=user_id,
            content=content,
            content_type=content_type,
            source="video-audio-uploads",
        )
        asset = UserAudioAsset(
            user_id=user_id,
            name=(filename or "参考音频").strip()[:255] or "参考音频",
            audio_url=uploaded.url,
            object_key=uploaded.object_key,
            duration_seconds=0,
            size=uploaded.size,
            content_type=uploaded.content_type,
            source="upload",
        )
        db.add(asset)
        await db.commit()
    except (ValueError, OssConfigError) as exc:
        return AudioUploadCreation(None, error_message=str(exc))
    except Exception:
        await db.rollback()
        return AudioUploadCreation(None, error_message="音频上传失败")
    return AudioUploadCreation(uploaded, asset_id=asset.id)
