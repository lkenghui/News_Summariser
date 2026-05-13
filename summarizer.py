import json
import anthropic

client = anthropic.Anthropic()

TOPICS = [
    "Artificial Intelligence",
    "Space & Astronomy",
    "Climate & Environment",
    "Medicine & Health",
    "Physics & Chemistry",
    "Biology & Evolution",
    "Technology & Computing",
    "Energy & Materials",
    "Neuroscience",
    "Other",
]

TOPIC_ICONS = {
    "Artificial Intelligence": "🤖",
    "Space & Astronomy": "🚀",
    "Climate & Environment": "🌍",
    "Medicine & Health": "💊",
    "Physics & Chemistry": "⚛️",
    "Biology & Evolution": "🧬",
    "Technology & Computing": "💻",
    "Energy & Materials": "⚡",
    "Neuroscience": "🧠",
    "Other": "📰",
}


def summarize_articles(articles: list[dict]) -> list[dict]:
    """Call Claude to summarize articles and assign topics. Returns enriched articles."""
    if not articles:
        return []

    articles_text = ""
    for i, a in enumerate(articles, start=1):
        articles_text += (
            f"Article {i}:\n"
            f"Title: {a['title']}\n"
            f"Source: {a['source']}\n"
            f"Preview: {a['description'][:400]}\n"
            "---\n"
        )

    topics_list = ", ".join(TOPICS)
    prompt = (
        f"You are curating a morning science & technology digest. "
        f"For each article below provide:\n"
        f"1. A concise 2-3 sentence summary capturing the key insight or finding.\n"
        f"2. The single best-matching topic from: {topics_list}\n\n"
        f"{articles_text}\n"
        f"Respond ONLY with a JSON array. Each element must have exactly these keys:\n"
        f'  "index" (integer, 1-based), "summary" (string), "topic" (string)\n'
        f"No markdown, no extra text — raw JSON only."
    )

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()

    # Strip optional markdown fences
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    summaries = json.loads(raw)
    summary_map = {int(s["index"]): s for s in summaries}

    enriched = []
    for i, article in enumerate(articles, start=1):
        meta = summary_map.get(i, {})
        topic = meta.get("topic", "Other")
        enriched.append({
            **article,
            "summary": meta.get("summary", article["description"][:300]),
            "topic": topic,
            "topic_icon": TOPIC_ICONS.get(topic, "📰"),
        })
    return enriched
