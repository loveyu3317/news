#!/usr/bin/env python3
"""Generate a daily U.S. news digest for GitHub issues."""

from __future__ import annotations

import argparse
import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo

import feedparser
from deep_translator import GoogleTranslator


@dataclass
class Article:
    source: str
    title_en: str
    summary_en: str
    link: str
    published: str
    title_zh: str = ""
    summary_zh: str = ""


RSS_SOURCES = {
    "Reuters Top News": "https://feeds.reuters.com/reuters/topNews",
    "NYTimes Home Page": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "Washington Post World": "https://feeds.washingtonpost.com/rss/world",
    "NPR News": "https://feeds.npr.org/1001/rss.xml",
    "CNN Top Stories": "http://rss.cnn.com/rss/edition.rss",
    "Fox News Latest": "https://moxie.foxnews.com/google-publisher/latest.xml",
}


def fetch_articles(limit_per_source: int) -> list[Article]:
    items: list[Article] = []
    for source, url in RSS_SOURCES.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:limit_per_source]:
            title = entry.get("title", "(No title)").strip()
            summary = entry.get("summary", "").strip()
            link = entry.get("link", "")
            published = entry.get("published", "")
            items.append(
                Article(
                    source=source,
                    title_en=title,
                    summary_en=strip_html(summary),
                    link=link,
                    published=published,
                )
            )
    return items


def strip_html(text: str) -> str:
    cleaned = text.replace("<p>", " ").replace("</p>", " ")
    for token in ["<br>", "<br/>", "<br />"]:
        cleaned = cleaned.replace(token, " ")
    return " ".join(cleaned.split())


def translate_articles(articles: Iterable[Article], target_lang: str = "zh-CN") -> None:
    translator = GoogleTranslator(source="auto", target=target_lang)
    for item in articles:
        try:
            item.title_zh = translator.translate(item.title_en)
        except Exception:
            item.title_zh = "[Translation failed]"
        try:
            short_summary = item.summary_en[:350]
            item.summary_zh = translator.translate(short_summary) if short_summary else ""
        except Exception:
            item.summary_zh = ""


def render_markdown(articles: list[Article], generated_at: str) -> str:
    lines = [
        "# Daily U.S. News Digest",
        "",
        f"Generated at (UTC): {generated_at}",
        "Target delivery time: 8:00 PM America/New_York",
        "",
        "This issue was created automatically by GitHub Actions.",
        "",
    ]

    for article in articles:
        lines.extend(
            [
                f"## {article.source}",
                "",
                f"**EN:** {article.title_en}",
                "",
                f"**ZH:** {article.title_zh or '[Translation unavailable]'}",
                "",
                f"**Published:** {article.published or 'Unknown'}",
                "",
                f"**Summary EN:** {article.summary_en[:280] or 'No summary available.'}",
                "",
                f"**Summary ZH:** {article.summary_zh[:280] or '[Translation unavailable]'}",
                "",
                f"Read more: {article.link}",
                "",
            ]
        )

    return "\n".join(lines).strip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate daily bilingual U.S. news digest")
    parser.add_argument("--limit-per-source", type=int, default=3)
    parser.add_argument("--only-at-hour", type=int, default=None, help="Only run when America/New_York hour matches")
    parser.add_argument("--force-run", action="store_true", help="Ignore the local-hour guard and run immediately")
    parser.add_argument("--title-output", default="issue_title.txt", help="File path for the issue title")
    parser.add_argument("--body-output", default="issue_body.md", help="File path for the issue markdown body")
    return parser.parse_args()


def write_output(path_str: str, content: str) -> None:
    path = Path(path_str)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.only_at_hour is not None and not args.force_run:
        ny_hour = dt.datetime.now(ZoneInfo("America/New_York")).hour
        if ny_hour != args.only_at_hour:
            print(f"Skip run because New York hour is {ny_hour}, expected {args.only_at_hour}.")
            return

    generated_at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    articles = fetch_articles(limit_per_source=args.limit_per_source)
    translate_articles(articles)

    today = dt.datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
    title = f"Daily U.S. News Digest - {today}"
    body = render_markdown(articles, generated_at)

    write_output(args.title_output, title + "\n")
    write_output(args.body_output, body)

    print(f"Wrote issue title to {args.title_output}")
    print(f"Wrote issue body to {args.body_output}")


if __name__ == "__main__":
    main()
