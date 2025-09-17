import re
from typing import Optional


def enforce_length_and_sanitize(text: str, max_chars: int = 800) -> str:
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_chars:
        return _cleanup(text)
    truncated = text[:max_chars]
    # avoid cutting inside open quotes/brackets at the tail
    truncated = _close_unclosed_pairs(truncated)
    return _cleanup(truncated)


def _cleanup(text: str) -> str:
    # remove markdown headers, links, hashtags
    text = re.sub(r"\s*^#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"https?://\S+", "", text)
    # remove hashtags (unicode-aware using \w which is unicode in py3)
    text = re.sub(r"(^|\s)#[\w_]+", r"\1", text)
    # collapse whitespace and stray punctuation
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([.,!?;:])", r"\1", text)
    return text.strip()


def _close_unclosed_pairs(text: str) -> str:
    pairs = [("\"", "\""), ("'", "'"), ("(", ")"), ("[", "]"), ("{", "}")]
    for open_ch, close_ch in pairs:
        if text.count(open_ch) > text.count(close_ch):
            text = text.rstrip() + close_ch
    return text


def mini_validator(text: str, language_hint: Optional[str]) -> bool:
    if not text or len(text) > 800:
        return False
    if "http" in text or "#" in text:
        return False
    if re.search(r"<[^>]+>", text):  # HTML tags
        return False
    # basic toxicity filter (very naive)
    bad_words = [
        "идиот", "тупой", "ненавижу", "суицид", "убить", "kill", "hate",
    ]
    lowered = text.lower()
    if any(bad in lowered for bad in bad_words):
        return False
    # language heuristic: if hint says 'en' but Cyrillic detected → fail
    if language_hint:
        if language_hint.lower().startswith("en") and re.search(r"[\u0400-\u04FF]", text):
            return False
    return True



