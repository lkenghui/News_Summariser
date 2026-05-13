import json
import os
import threading
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for

load_dotenv()

from database import init_db, has_seen, mark_seen, save_digest, get_latest_digest
from fetcher import fetch_articles
from summarizer import summarize_articles

app = Flask(__name__)
app.secret_key = os.urandom(24)

init_db()

BATCH_SIZE = 10  # Max articles per Claude call

# Track background job state
_job_running = False
_job_lock = threading.Lock()


def _group_by_topic(articles: list[dict]) -> dict:
    groups: dict[str, list] = {}
    for article in articles:
        topic = article.get("topic", "Other")
        groups.setdefault(topic, []).append(article)
    return dict(sorted(groups.items(), key=lambda kv: len(kv[1]), reverse=True))


def _run_digest_job():
    global _job_running
    try:
        all_articles = fetch_articles(max_per_feed=20)
        new_articles = [a for a in all_articles if not has_seen(a["url"])]

        if not new_articles:
            return

        enriched: list[dict] = []
        for i in range(0, len(new_articles), BATCH_SIZE):
            batch = new_articles[i: i + BATCH_SIZE]
            try:
                enriched.extend(summarize_articles(batch))
            except Exception as exc:
                print(f"[summarizer] Batch {i // BATCH_SIZE + 1} failed: {exc}")
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
    except Exception as exc:
        print(f"[digest job] Failed: {exc}")
    finally:
        with _job_lock:
            _job_running = False


def start_digest_job():
    global _job_running
    with _job_lock:
        if _job_running:
            return False
        _job_running = True
    t = threading.Thread(target=_run_digest_job, daemon=True)
    t.start()
    return True


@app.route("/")
def index():
    row = get_latest_digest()
    if row:
        articles_json, generated_at = row
        groups = _group_by_topic(json.loads(articles_json))
        total = sum(len(v) for v in groups.values())
        return render_template(
            "digest.html",
            groups=groups,
            generated_at=generated_at,
            total_articles=total,
            date=datetime.now().strftime("%A, %B %d, %Y"),
            loading=False,
        )
    # No digest yet — start a job and show loading page
    start_digest_job()
    return render_template("loading.html", date=datetime.now().strftime("%A, %B %d, %Y"))


@app.route("/refresh")
def refresh():
    start_digest_job()
    return render_template("loading.html", date=datetime.now().strftime("%A, %B %d, %Y"))


@app.route("/status")
def status():
    with _job_lock:
        running = _job_running
    return {"running": running}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=False, host="0.0.0.0", port=port)
