#!/usr/bin/env python3
"""Разметить старую CV-библиотеку: золотой фонд / свежее / архив + звёзды как в Word-отчёте.

Новый collect.py не трогаем.
"""

from __future__ import annotations

import json
from pathlib import Path

STS = Path(r"C:\Users\Mariyaa\Desktop\скрипты\LLM\work\Sts")
SRC = STS / "arxiv_articles_enriched.json"
TOP = STS / "arxiv_articles_top20.json"
FRESH_FROM = "2025-01-01"


def stars_from_scores(article: dict, shelf: str) -> int:
    work = int(article.get("work_relevance_score") or 0)
    found = int(article.get("foundational_score") or 0)
    pri = int(article.get("priority_score") or 0)
    title = f"{article.get('article') or ''} {article.get('title_ru') or ''}".lower()
    survey = "survey" in title or "обзор" in title
    top = bool(article.get("top20_candidate"))

    if shelf == "archive":
        if work >= 80:
            return 2
        return 1

    if shelf == "golden":
        if survey or found >= 82 or (top and (article.get("top20_rank") or 99) <= 6):
            return 5
        if top or found >= 72 or work >= 88:
            return 4
        return 3

    score = max(work, pri)
    if score >= 88:
        return 5
    if score >= 78:
        return 4
    if score >= 68:
        return 3
    if score >= 58:
        return 2
    return 1


def shelf_of(article: dict) -> str:
    day = str(article.get("date") or "")[:10]
    title = f"{article.get('article') or ''} {article.get('title_ru') or ''}".lower()
    survey = "survey" in title or "обзор" in title
    found = int(article.get("foundational_score") or 0)
    role = article.get("_reading_role") or ""

    if day >= FRESH_FROM:
        return "fresh"
    if article.get("top20_candidate"):
        return "golden"
    if survey or found >= 75 or role == "FOUNDATION":
        return "golden"
    if day >= "2023-01-01" and int(article.get("work_relevance_score") or 0) >= 90:
        return "golden"
    return "archive"


def rec_of(shelf: str, stars: int) -> str:
    if shelf == "archive":
        return "REFERENCE_ONLY"
    if shelf == "golden":
        return "GOLDEN" if stars >= 4 else "SELECTIVE_READ"
    if stars >= 4:
        return "READ_NOW"
    if stars == 3:
        return "READ_NEXT"
    return "SELECTIVE_READ"


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    counts = {"golden": 0, "fresh": 0, "archive": 0}
    star_hist = {i: 0 for i in range(1, 6)}

    for article in data:
        shelf = shelf_of(article)
        n = stars_from_scores(article, shelf)
        article["shelf"] = shelf
        article["shelf_label"] = {
            "golden": "Золотой фонд",
            "fresh": "Свежее",
            "archive": "Архив",
        }[shelf]
        article["importance_stars"] = n
        article["importance_mark"] = "★" * n + "☆" * (5 - n)
        article["_recommendation"] = rec_of(shelf, n)
        if shelf == "golden":
            article["_reason_shelf"] = "Канон: обзор, фундамент или проверенный visual prompting. Не новость недели."
        elif shelf == "fresh":
            article["_reason_shelf"] = "2025–2026: текущий слой для очереди чтения."
        else:
            article["_reason_shelf"] = "Оставить в полной библиотеке; не тащить в очередь «читать сейчас»."
        counts[shelf] += 1
        star_hist[n] += 1

    SRC.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    if TOP.exists():
        top = json.loads(TOP.read_text(encoding="utf-8"))
        by_id = {str(a.get("arxiv_id")): a for a in data}
        for item in top:
            src = by_id.get(str(item.get("arxiv_id")))
            if not src:
                continue
            for key in ("shelf", "shelf_label", "importance_stars", "importance_mark", "_recommendation", "_reason_shelf"):
                item[key] = src.get(key)
        TOP.write_text(json.dumps(top, ensure_ascii=False, indent=2), encoding="utf-8")

    print("written", SRC)
    print("shelf", counts)
    print("stars", star_hist)


if __name__ == "__main__":
    main()
