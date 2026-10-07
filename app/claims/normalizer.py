import re

from app.normalization import normalize_text


def normalize_claim(text):
    return re.sub(r"[^\w\s.%+-]", "", normalize_text(text).lower()).strip()
