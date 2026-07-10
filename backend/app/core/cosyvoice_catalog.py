from __future__ import annotations

from html.parser import HTMLParser
import re


COSYVOICE_V3_FLASH = "cosyvoice-v3-flash"
COSYVOICE_VOICE_LIST_URL = "https://help.aliyun.com/zh/model-studio/cosyvoice-voice-list"
EXPECTED_V3_FLASH_VOICE_COUNT = 88


def _clean_text(value: str) -> str:
    value = value.replace("\xa0", " ")
    value = re.sub(r"[ \t\r]+", " ", value)
    return "\n".join(line.strip() for line in value.splitlines() if line.strip())


class _CosyVoiceTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[tuple[list[str], str]] = []
        self._heading_parts: list[str] | None = None
        self._in_target_section = False
        self._in_row = False
        self._in_cell = False
        self._cells: list[str] = []
        self._cell_parts: list[str] = []
        self._audio_url = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = dict(attrs)
        if tag == "h2":
            self._heading_parts = []
            return
        if not self._in_target_section:
            return
        if tag == "tr":
            self._in_row = True
            self._cells = []
            self._audio_url = ""
        elif self._in_row and tag in {"td", "th"}:
            self._in_cell = True
            self._cell_parts = []
        elif self._in_row and tag == "audio":
            self._audio_url = attrs_map.get("src") or attrs_map.get("data-src") or self._audio_url
        elif self._in_row and tag == "source":
            self._audio_url = attrs_map.get("src") or attrs_map.get("data-src") or self._audio_url
        elif self._in_cell and tag == "br":
            self._cell_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._heading_parts is not None:
            self._heading_parts.append(data)
        if self._in_cell:
            self._cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "h2" and self._heading_parts is not None:
            heading = _clean_text("".join(self._heading_parts))
            self._in_target_section = heading.startswith(COSYVOICE_V3_FLASH)
            self._heading_parts = None
            return
        if not self._in_target_section:
            return
        if self._in_cell and tag in {"p", "div", "li"}:
            self._cell_parts.append("\n")
        if self._in_row and tag in {"td", "th"}:
            self._cells.append(_clean_text("".join(self._cell_parts)))
            self._cell_parts = []
            self._in_cell = False
        elif self._in_row and tag == "tr":
            self.rows.append((self._cells, self._audio_url))
            self._in_row = False


def _field(text: str, label: str) -> str:
    match = re.search(rf"{label}\s*：\s*([^\n]+)", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", "", match.group(1)) if match else ""


def _supported(text: str, label: str) -> bool:
    match = re.search(rf"{label}\s*：\s*(支持|不支持)", text, flags=re.IGNORECASE)
    return bool(match and match.group(1) == "支持")


def parse_cosyvoice_v3_flash_voices(html: str) -> list[dict]:
    parser = _CosyVoiceTableParser()
    parser.feed(html)

    voices: list[dict] = []
    category = ""
    for cells, preview_audio_url in parser.rows:
        if len(cells) not in {4, 5}:
            continue
        if len(cells) == 5:
            category = cells[0]
            info, features = cells[1], cells[2]
        else:
            info, features = cells[0], cells[1]
        voice_id = _field(info, r"voice\s*参数")
        if not voice_id:
            continue
        voices.append(
            {
                "model_id": COSYVOICE_V3_FLASH,
                "voice_id": voice_id,
                "name": _field(info, "名称"),
                "category": category,
                "trait": _field(info, "特质"),
                "age_range": _field(info, "年龄"),
                "languages": _field(info, "语言"),
                "supports_ssml": _supported(features, "SSML"),
                "supports_instruct": _supported(features, "Instruct"),
                "supports_timestamp": _supported(features, "时间戳"),
                "regions": cells[-1].replace(" ", ""),
                "preview_audio_url": preview_audio_url,
                "enabled": True,
                "sort_order": (len(voices) + 1) * 10,
            }
        )
    return voices


def validate_cosyvoice_v3_flash_voices(voices: list[dict]) -> None:
    if len(voices) != EXPECTED_V3_FLASH_VOICE_COUNT:
        raise ValueError(
            f"CosyVoice音色数量异常：期望{EXPECTED_V3_FLASH_VOICE_COUNT}，实际{len(voices)}"
        )
    voice_ids = [voice["voice_id"] for voice in voices]
    if len(set(voice_ids)) != len(voice_ids):
        raise ValueError("CosyVoice音色存在重复voice_id")
    required_fields = ("voice_id", "name", "category", "preview_audio_url")
    for voice in voices:
        missing = [field for field in required_fields if not voice[field]]
        if missing:
            raise ValueError(f"CosyVoice音色{voice['voice_id']}缺少字段：{','.join(missing)}")
