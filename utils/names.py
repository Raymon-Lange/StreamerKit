from __future__ import annotations

import re
import unicodedata


def normalize_name(name: str) -> str:
    if not name:
        return ""
    cleaned = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode("ascii")
    cleaned = cleaned.replace("’", "'").replace("‘", "'")
    cleaned = cleaned.lower().replace("jr.", "jr").replace("sr.", "sr")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return re.sub(r"[^a-z0-9 ]", "", cleaned).strip()


def clean_player_name(name: str) -> str:
    if not name:
        return ""
    cleaned = name.replace("/td>", " ").replace("/td&gt;", " ")
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = re.sub(r"\*+$", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned
