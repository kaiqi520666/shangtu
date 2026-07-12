import httpx
import pytest
from fastapi import Depends, FastAPI

from app.core.media_download import remote_media_download_response
from app.core.pagination import PaginationParams, create_pagination_params


def test_remote_media_download_uses_url_extension_without_query_string():
    response = remote_media_download_response(
        "https://cdn.example.com/video/result.webm?token=secret",
        filename_stem="task-1",
        fallback_extension="mp4",
    )

    assert response.media_type == "video/webm"
    assert response.headers["content-disposition"] == 'attachment; filename="task-1.webm"'


def test_remote_media_download_allows_audio_media_type_override():
    response = remote_media_download_response(
        "https://cdn.example.com/audio/result.webm",
        filename_stem="audio-1",
        fallback_extension="webm",
        media_type_override="audio/webm",
    )

    assert response.media_type == "audio/webm"


def test_pagination_params_exposes_offset():
    pagination = PaginationParams(page=3, page_size=20)

    assert pagination.offset == 40


@pytest.mark.asyncio
async def test_pagination_dependency_applies_custom_defaults_and_limits():
    app = FastAPI()
    dependency = create_pagination_params(default_page_size=12, max_page_size=50)

    @app.get("/items")
    def list_items(pagination: PaginationParams = Depends(dependency)):
        return {"page": pagination.page, "page_size": pagination.page_size}

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        assert (await client.get("/items")).json() == {"page": 1, "page_size": 12}
        assert (await client.get("/items?page=2&page_size=50")).json() == {
            "page": 2,
            "page_size": 50,
        }
        assert (await client.get("/items?page=0")).status_code == 422
        assert (await client.get("/items?page_size=51")).status_code == 422
