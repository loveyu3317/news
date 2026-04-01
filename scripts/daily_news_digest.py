#!/usr/bin/env python3
"""Daily U.S. news digest (EN+ZH) and email sender."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import smtplib
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
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
            item.title_zh = "[翻译失败 / Translation failed]"
        try:
            short_summary = item.summary_en[:350]
            item.summary_zh = translator.translate(short_summary) if short_summary else ""
        except Exception:
            item.summary_zh = ""


def render_html(articles: list[Article], generated_at: str) -> str:
    blocks: list[str] = []
    for article in articles:
        blocks.append(
            f"""
            <li style=\"margin-bottom:14px;\">
              <strong>{escape(article.source)}</strong><br/>
              <b>EN:</b> {escape(article.title_en)}<br/>
              <b>中文:</b> {escape(article.title_zh)}<br/>
              <small>{escape(article.published)}</small><br/>
              <b>Summary EN:</b> {escape(article.summary_en[:280])}<br/>
              <b>摘要中文:</b> {escape(article.summary_zh[:280])}<br/>
              <a href=\"{escape(article.link)}\">Read more</a>
            </li>
            """
        )

    return f"""
    <html>
      <body style=\"font-family:Arial,sans-serif;\">
        <h2>Daily U.S. News Digest / 美国新闻每日摘要</h2>
        <p>
          Generated at (UTC): {escape(generated_at)}<br/>
          Trigger time target: 8:00 PM America/New_York
        </p>
        <ul>
          {''.join(blocks)}
        </ul>
      </body>
    </html>
    """


def send_email(subject: str, html_body: str) -> None:
    smtp_host = required_env("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = required_env("SMTP_USERNAME")
    smtp_pass = required_env("SMTP_PASSWORD")
    mail_from = required_env("MAIL_FROM")
    mail_to = required_env("MAIL_TO")

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = mail_from
    message["To"] = mail_to
    message.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(mail_from, [mail_to], message.as_string())


def required_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send daily bilingual US news digest")
    parser.add_argument("--limit-per-source", type=int, default=3)
    parser.add_argument("--only-at-hour", type=int, default=None, help="Only send when America/New_York hour matches")
    parser.add_argument("--force-run", action="store_true", help="Ignore the local-hour guard and send immediately")
    return parser.parse_args()


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

    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    subject = f"Daily US News Digest / 美国新闻摘要 - {today}"
    body = render_html(articles, generated_at)
    send_email(subject, body)


if __name__ == "__main__":
    main()
