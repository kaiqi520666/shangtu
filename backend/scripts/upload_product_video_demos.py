from __future__ import annotations

import json
import mimetypes
import sys
from pathlib import Path

import oss2

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DEMO_DIR = Path("/tmp/shangtu-product-video-demos")

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.oss import build_public_url, get_oss_config  # noqa: E402

OSS_PREFIX = "system/product-video-demos"

VIDEO_TYPES = [
    {
        "type_id": "ugc_seeding",
        "title": "UGC 种草",
        "subtitle": "用户视角真实分享体验",
        "input_mode": "image_to_video",
    },
    {
        "type_id": "short_drama",
        "title": "带货短剧",
        "subtitle": "短剧情节植入产品",
        "input_mode": "reference_to_video",
    },
    {
        "type_id": "product_demo",
        "title": "产品演示",
        "subtitle": "多角度展示 + 使用演示",
        "input_mode": "reference_to_video",
    },
    {
        "type_id": "product_talk",
        "title": "产品口播",
        "subtitle": "面对镜头讲解产品卖点",
        "input_mode": "image_to_video",
    },
    {
        "type_id": "tvc_ad",
        "title": "TVC广告",
        "subtitle": "品牌广告片质感",
        "input_mode": "reference_to_video",
    },
    {
        "type_id": "pain_solution",
        "title": "痛点解决",
        "subtitle": "痛点场景到产品解决",
        "input_mode": "reference_to_video",
    },
    {
        "type_id": "unboxing",
        "title": "开箱种草",
        "subtitle": "第一视角拆包惊喜体验",
        "input_mode": "reference_to_video",
    },
    {
        "type_id": "reaction",
        "title": "反应展示",
        "subtitle": "首次使用惊喜反应",
        "input_mode": "reference_to_video",
    },
]


def upload_file(bucket: oss2.Bucket, config: dict[str, str], path: Path, object_key: str) -> str:
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    bucket.put_object_from_file(
        object_key,
        str(path),
        headers={
            "Content-Type": content_type,
            "Cache-Control": "public, max-age=31536000, immutable",
        },
    )
    return build_public_url(object_key, config)


def main() -> None:
    demo_dir = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else DEFAULT_DEMO_DIR
    video_dir = demo_dir / "videos"
    poster_dir = demo_dir / "posters"
    if not video_dir.exists() or not poster_dir.exists():
        raise RuntimeError(f"演示视频目录不完整: {demo_dir}")

    config = get_oss_config()
    auth = oss2.Auth(config["access_key_id"], config["access_key_secret"])
    bucket = oss2.Bucket(auth, config["endpoint"], config["bucket_name"])

    manifest = []
    for item in VIDEO_TYPES:
        type_id = item["type_id"]
        video_path = video_dir / f"{type_id}.mp4"
        poster_path = poster_dir / f"{type_id}.jpg"
        if not video_path.exists():
            raise RuntimeError(f"缺少演示视频: {video_path}")
        if not poster_path.exists():
            raise RuntimeError(f"缺少演示封面: {poster_path}")

        video_key = f"{OSS_PREFIX}/videos/{type_id}.mp4"
        poster_key = f"{OSS_PREFIX}/posters/{type_id}.jpg"
        video_url = upload_file(bucket, config, video_path, video_key)
        poster_url = upload_file(bucket, config, poster_path, poster_key)
        manifest.append(
            {
                **item,
                "video_url": video_url,
                "poster_url": poster_url,
                "video_object_key": video_key,
                "poster_object_key": poster_key,
            }
        )

    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
