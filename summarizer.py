import json
import os

from openai import OpenAI

_client = None
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")

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


def get_client() -> OpenAI:
    global _client
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not configured. Add it to .env to generate AI summaries.")
    if _client is None:
        _client = OpenAI()
    return _client


def summarize_articles(articles: list[dict]) -> list[dict]:
    """Call OpenAI to summarize articles and assign topics. Returns enriched articles."""
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
        f"Return structured JSON only."
    )

    response = get_client().responses.create(
        model=OPENAI_MODEL,
        input=[
            {
                "role": "system",
                "content": (
                    "You write accurate, concise science and technology news summaries. "
                    "Use only the supplied article title, source, and preview. "
                    "Choose exactly one topic from the provided topic list."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        max_output_tokens=4096,
        text={
            "format": {
                "type": "json_schema",
                "name": "article_summaries",
                "strict": True,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "summaries": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "index": {
                                        "type": "integer",
                                        "description": "The 1-based article index from the input.",
                                    },
                                    "summary": {
                                        "type": "string",
                                        "description": "A concise 2-3 sentence summary.",
                                    },
                                    "topic": {
                                        "type": "string",
                                        "enum": TOPICS,
                                    },
                                },
                                "required": ["index", "summary", "topic"],
                            },
                        }
                    },
                    "required": ["summaries"],
                },
            }
        },
    )

    raw = response.output_text.strip()

    # Strip optional markdown fences
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    summaries_payload = json.loads(raw)
    summaries = summaries_payload.get("summaries", [])
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
