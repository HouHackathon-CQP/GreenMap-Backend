import asyncio
import unicodedata
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from typing import Iterable

import httpx
from fastapi import HTTPException

from app.schemas import NewsItem

HANOIMOI_FEEDS = [
    "https://hanoimoi.vn/rss/do-thi/giao-thong",
    "https://hanoimoi.vn/rss/kinh-te",
    "https://hanoimoi.vn/rss/do-thi/moi-truong",
    "https://hanoimoi.vn/rss/y-te",
    "https://hanoimoi.vn/rss/du-lich",
    "https://hanoimoi.vn/rss/nong-nghiep-nong-thon",
    "https://hanoimoi.vn/rss/khoa-hoc-cong-nghe/chuyen-doi-so",
]

HANOI_KEYWORDS = ["a"]
TOPIC_KEYWORDS = [
    "a"
]


def _normalize(text: str | None) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFD", text)
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return ascii_text.lower()


def _contains_hanoi(text: str, link: str, categories: list[str]) -> bool:
    normalized_text = _normalize(text)
    normalized_categories = _normalize(" ".join(categories))
    if any(city in normalized_text for city in HANOI_KEYWORDS):
        return True
    if any(city in normalized_categories for city in HANOI_KEYWORDS):
        return True
    link_lower = (link or "").lower()
    return "ha-noi" in link_lower or "hanoimoi" in link_lower


def _match_topics(text: str, link: str, categories: list[str]) -> bool:
    combined = " ".join([text, " ".join(categories)])
    normalized = _normalize(combined)
    has_topic = any(keyword in normalized for keyword in TOPIC_KEYWORDS)
    has_city = _contains_hanoi(text, link, categories)
    return has_topic and has_city


def _parse_feed(xml_content: str) -> Iterable[NewsItem]:
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=502, detail="RSS VNExpress trả về dữ liệu lỗi") from exc

    for item in root.findall(".//item"):
        title = item.findtext("title") or ""
        description = item.findtext("description")
        link = item.findtext("link") or ""
        categories = [c.text or "" for c in item.findall("category")]
        pub_date_raw = item.findtext("pubDate")
        published_at = None
        if pub_date_raw:
            try:
                published_at = parsedate_to_datetime(pub_date_raw)
            except (TypeError, ValueError):
                published_at = None

        if not _match_topics(f"{title} {description}", link, categories):
            continue

        if link:
            yield NewsItem(
                title=title.strip(),
                description=description.strip() if description else None,
                link=link.strip(),
                published_at=published_at,
            )


async def _fetch_feed(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        response = await client.get(url, timeout=10.0)
        response.raise_for_status()
        return response.text
    except httpx.RequestError:
        return None
    except httpx.HTTPStatusError:
        return None


async def fetch_hanoimoi_environment_news(limit: int = 20) -> list[NewsItem]:
    async with httpx.AsyncClient() as client:
        tasks = [_fetch_feed(client, url) for url in HANOIMOI_FEEDS]
        feed_contents = await asyncio.gather(*tasks)

    articles: dict[str, NewsItem] = {}
    for content in feed_contents:
        if not content:
            continue
        for article in _parse_feed(content):
            articles.setdefault(article.link, article)

    sorted_articles = sorted(
        articles.values(),
        key=lambda a: a.published_at or parsedate_to_datetime("Thu, 01 Jan 1970 00:00:00 GMT"),
        reverse=True,
    )
    return sorted_articles[:limit]
