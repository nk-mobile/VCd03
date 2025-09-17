import argparse
import os
import sys
from typing import Optional

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

from .extract import fetch_and_extract
from .model import generate_post_via_openai
from .prompt import build_system_prompt, build_user_prompt
from .validator import enforce_length_and_sanitize, mini_validator
from .utils import detect_language, safe_print_stderr


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agent-post",
        description=(
            "Консольный инструмент: по URL страницы сгенерировать короткий пост (≤800 символов)."
        ),
    )
    parser.add_argument("url", help="URL страницы")
    parser.add_argument(
        "--style",
        default="ироничный",
        help="Переменная STYLE: стиль текста (по умолчанию: ироничный)",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("AGENT_MODEL", "gpt-4o-mini"),
        help="Имя модели OpenAI (можно через env AGENT_MODEL)",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("OPENAI_API_KEY"),
        help="Ключ OpenAI API (по умолчанию из OPENAI_API_KEY)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Таймаут сети для загрузки страницы, сек (по умолчанию 20)",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=800,
        help="Максимальная длина поста (по умолчанию 800)",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Желаемый язык поста (иначе определяется по странице/эвристикам)",
    )

    args = parser.parse_args(argv)

    # if no explicit --api-key, try env after loading .env
    if not args.api_key and not os.environ.get("OPENAI_API_KEY"):
        safe_print_stderr(
            "[agent] Предупреждение: переменная OPENAI_API_KEY не установлена."
        )

    extract = fetch_and_extract(args.url, timeout=args.timeout)

    # Language detection: prefer explicit, else from extract, else heuristic.
    language = args.language or detect_language(
        extract.text, extract.meta.get("lang") or extract.language
    )

    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(
        style=args.style,
        url=extract.url,
        title=extract.title,
        language=language,
        meta=extract.meta,
        text=extract.text,
    )

    try:
        raw = generate_post_via_openai(
            api_key=args.api_key,
            model=args.model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
    except Exception as exc:  # network or API error
        safe_print_stderr(f"[agent] Ошибка API: {exc}")
        raw = _fallback_post(extract.title, extract.url, language, args.style)

    sanitized = enforce_length_and_sanitize(raw, max_chars=args.max_chars)
    # mini validation; if fails, soften with fallback composed from page context
    if not mini_validator(sanitized, language):
        sanitized = _fallback_post(extract.title, extract.url, language, args.style)
        sanitized = enforce_length_and_sanitize(sanitized, max_chars=args.max_chars)

    # Print only the post text
    print(sanitized)
    return 0


def _fallback_post(title: str, url: str, language: str, style: str) -> str:
    # Safe neutral post without unverifiable facts
    domain = url.split("//")[-1].split("/")[0]
    if language and language.lower().startswith("en"):
        return (
            f"Topic: {title or 'the page'}. A brief overview without claims: "
            f"key points are hinted but not asserted. If you're exploring {domain}, "
            f"it may be worth a look — style: {style}."
        )
    # default to Russian
    return (
        f"Тема: {title or 'страница'}. Короткий обзор без лишних утверждений: "
        f"подсвечиваем интерес, но без деталей. Если изучаете {domain}, "
        f"можно присмотреться — стиль: {style}."
    )


if __name__ == "__main__":
    sys.exit(main())


