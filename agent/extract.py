from dataclasses import dataclass
from typing import Dict, Optional

import requests
from bs4 import BeautifulSoup  # type: ignore


@dataclass
class Extract:
    url: str
    title: str
    language: str
    text: str
    meta: Dict[str, str]


def fetch_and_extract(url: str, timeout: float = 20.0) -> Extract:
    resp = requests.get(url, timeout=timeout, headers={
        "User-Agent": "Mozilla/5.0 (compatible; AgentPost/0.1; +https://example.local)"
    })
    resp.raise_for_status()

    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    lang = soup.html.get("lang") if soup.html else ""
    meta: Dict[str, str] = {}

    # Collect meta tags of interest
    for tag in soup.find_all("meta"):
        name = tag.get("name") or tag.get("property")
        content: Optional[str] = tag.get("content")
        if name and content:
            meta[name] = content

    # Visible text extraction with basic cleanup
    for bad in soup(["script", "style", "noscript", "template"]):
        bad.decompose()
    text = soup.get_text(" ")
    text = " ".join(text.split())

    return Extract(url=url, title=title, language=lang or "", text=text, meta=meta)


