from app.core.media_download import remote_media_download_response
from app.core.pagination import PaginationParams


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
