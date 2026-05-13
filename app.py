import json
import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash

load_dotenv()

from database import init_db, has_seen, mark_seen, save_digest, get_latest_digest
from fetcher import fetch_articles
from summarizer import summarize_articles

app = Flask(__name__)
app.secret_key = os.urandom(24)

BATCH_SIZE = 15  # Max articles per Claude call


def _group_by_topic(articles: list[dict]) -> dict:
    groups: dict[str, list] = {}
    for article in articles:
        topic = article.get("topic", "Other")
        groups.setdefault(topic, []).append(article)
    # Sort topics by article count descending
    return dict(sorted(groups.items(), key=lambda kv: len(kv[1]), reverse=True))


def build_digest(force: bool = False) -> tuple[dict, str | None, bool]:
    """
    Returns (grouped_articles, generated_at_str, is_fresh).
    is_fresh = True when new articles were fetched this call.
    """
    if not force:
        row = get_latest_digest()
        if row:
            articles_json, created_at = row
            return _group_by_topic(json.loads(articles_json)), created_at, False

    # Fetch from RSS
    all_articles = fetch_articles(max_per_feed=20)
    new_articles = [a for a in all_articles if not has_seen(a["url"])]

    if not new_articles:
        row = get_latest_digest()
        if row:
            articles_json, created_at = row
            return _group_by_topic(json.loads(articles_json)), created_at, False
        return {}, None, False

    # Summarize in batches
    enriched: list[dict] = []
    for i in range(0, len(new_articles), BATCH_SIZE):
        batch = new_articles[i : i + BATCH_SIZE]
        try:
            enriched.extend(summarize_articles(batch))
        except Exception as exc:
            print(f"[summarizer] Batch {i // BATCH_SIZE + 1} failed: {exc}")
            # Fall back: add unsummarized articles with description as summary
            for a in batch:
                enriched.append({
                    **a,
                    "summary": a.get("description", "")[:300],
                    "topic": "Other",
                    "topic_icon": "📰",
                })

    for article in enriched:
        mark_seen(article["url"], article["title"])

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_digest(json.dumps(enriched))
    return _group_by_topic(enriched), now, True


@app.route("/")
def index():
    groups, generated_at, is_fresh = build_digest(force=False)
    total = sum(len(v) for v in groups.values())
    return render_template(
        "digest.html",
        groups=groups,
        generated_at=generated_at,
        total_articles=total,
        date=datetime.now().strftime("%A, %B %d, %Y"),
        is_fresh=is_fresh,
    )


@app.route("/refresh")
def refresh():
    build_digest(force=True)
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=False, host="0.0.0.0", port=port)
