import pytest

from app.core.cosyvoice_catalog import (
    parse_cosyvoice_v3_flash_voices,
    validate_cosyvoice_v3_flash_voices,
)


HTML = """
<h2>cosyvoice-v3-flash音色列表</h2>
<table><tbody>
<tr><td>适用场景</td><td>音色信息</td><td>特性支持</td><td>试听</td><td>地域</td></tr>
<tr><td rowspan="2">社交陪伴</td><td><p>名称：龙安洋</p><p>voice 参数：longanyang</p><p>特质：阳光大男孩</p><p>年龄：20~30 岁</p><p>语言：中文（普通话）、英文</p></td><td><p>SSML：支持</p><p>Instruct：支持</p><p>时间戳：支持</p></td><td><audio src="https://example.com/longanyang.mp3"></audio></td><td>华北2（北京）、新加坡</td></tr>
<tr><td><p>名称：龙安欢</p><p>voice参数：longanhuan</p><p>特质：欢脱元气女</p><p>年龄：20~30岁</p><p>语言：中文（普通话）、英文</p></td><td><p>SSML：支持</p><p>Instruct：不支持</p><p>时间戳：支持</p></td><td><audio data-src="https://example.com/longanhuan.mp3"></audio></td><td>华北2（北京）</td></tr>
</tbody></table>
<h2>cosyvoice-v3-plus音色列表</h2>
"""


def test_parse_cosyvoice_voice_rows_and_rowspan_category():
    voices = parse_cosyvoice_v3_flash_voices(HTML)

    assert len(voices) == 2
    assert voices[0] == {
        "model_id": "cosyvoice-v3-flash",
        "voice_id": "longanyang",
        "name": "龙安洋",
        "category": "社交陪伴",
        "trait": "阳光大男孩",
        "age_range": "20~30岁",
        "languages": "中文（普通话）、英文",
        "supports_ssml": True,
        "supports_instruct": True,
        "supports_timestamp": True,
        "regions": "华北2（北京）、新加坡",
        "preview_audio_url": "https://example.com/longanyang.mp3",
        "enabled": True,
        "sort_order": 10,
    }
    assert voices[1]["category"] == "社交陪伴"
    assert voices[1]["supports_instruct"] is False
    assert voices[1]["preview_audio_url"] == "https://example.com/longanhuan.mp3"


def test_validate_rejects_incomplete_catalog():
    with pytest.raises(ValueError, match="数量异常"):
        validate_cosyvoice_v3_flash_voices([])
