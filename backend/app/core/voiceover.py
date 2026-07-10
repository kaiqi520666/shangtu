import math
import re

from app.core.cosyvoice_catalog import COSYVOICE_V3_FLASH

VOICEOVER_TEXT_LIMIT = 5000
VOICEOVER_FORMAT = "mp3"
VOICEOVER_SAMPLE_RATE = 24000


def count_voiceover_characters(text: str) -> int:
    return len(re.sub(r"\s", "", text))


def calculate_voiceover_credit_cost(character_count: int, unit_cost: int) -> int:
    return math.ceil(character_count / 100) * unit_cost
