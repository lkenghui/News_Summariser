import re
import feedparser

FEEDS = [
    {
        'name': 'MIT Technology Review',
        'url': 'https://www.technologyreview.com/feed/',
        'color': '#e8393a',
        'text_color': '#ffffff',
    },
    {
        'name': 'Science',
        'url': 'https://www.science.org/rss/news_current.xml',
        'color': '#0072b6',
        'text_color': '#ffffff',
    },
    {
        'name': 'Nature',
        'url': 'https://feeds.nature.com/nature/rss/current',
        'color': '#2d6a4f',
        'text_color': '#ffffff',
    },
]


def _strip_html(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def fetch_articles(max_per_feed: int = 20) -> list[dict]:
    articles = []
    for feed_info in FEEDS:
        try:
            feed = feedparser.parse(feed_info['url'])
            entries = feed.entries[:max_per_feed]
            for entry in entries:
                url = entry.get('link', '').strip()
                if not url:
                    continue

                title = _strip_html(entry.get('title', 'Untitled')).strip()

                # Try multiple fields for a content preview
                description = ''
                for field in ('summary', 'description', 'content'):
                    val = entry.get(field, '')
                    if isinstance(val, list) and val:
                        val = val[0].get('value', '')
                    if val:
                        description = _strip_html(str(val))[:600]
                        break

                articles.append({
                    'url': url,
                    'title': title,
                    'description': description,
                    'source': feed_info['name'],
                    'source_color': feed_info['color'],
                    'source_text_color': feed_info['text_color'],
                    'published': entry.get('published', ''),
                })
        except Exception as exc:
            print(f"[fetcher] Error fetching {feed_info['name']}: {exc}")

    return articles
