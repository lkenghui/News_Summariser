# News Summariser

Flask app that builds a science and technology morning digest from MIT Technology Review, Science, and Nature feeds.

## Setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Set `OPENAI_API_KEY` in `.env` before generating fresh AI summaries. You can optionally set `OPENAI_MODEL`; the default is `gpt-5.2`.

## Run

```bash
.venv/bin/python app.py
```

The app starts at `http://127.0.0.1:8080/`.

## Without An API Key

The app can display the latest saved digest without an API key. If you refresh and OpenAI is unavailable or not configured, it falls back to source-provided article descriptions and keeps the page usable.

## Test

```bash
.venv/bin/python -m unittest discover
```

Do not commit `.env`, `digest.db`, virtual environments, bytecode caches, or `.DS_Store`.
