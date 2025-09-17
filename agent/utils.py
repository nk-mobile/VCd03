import sys
from typing import Optional


def safe_print_stderr(message: str) -> None:
    try:
        print(message, file=sys.stderr)
    except Exception:
        pass


def detect_language(text: str, hint: Optional[str] = None) -> str:
    if hint:
        return hint
    # Simplified heuristic: detect Cyrillic → ru, Latin+ → en
    if any("\u0400" <= ch <= "\u04FF" for ch in text):
        return "ru"
    if any("A" <= ch <= "Z" or "a" <= ch <= "z" for ch in text):
        return "en"
    return "ru"  # default



