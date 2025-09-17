from typing import Optional

from openai import OpenAI  # type: ignore


def generate_post_via_openai(
    *,
    api_key: Optional[str],
    model: str,
    system_prompt: str,
    user_prompt: str,
) -> str:
    client = OpenAI(
        api_key=api_key,
        base_url="https://openai.api.proxyapi.ru/v1",
    ) if api_key is not None else OpenAI(base_url="https://openai.api.proxyapi.ru/v1")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=500,
    )
    content = response.choices[0].message.content or ""
    return content.strip()


