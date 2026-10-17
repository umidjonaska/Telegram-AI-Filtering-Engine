# Telegram AI Filtering Engine

[![CI](https://github.com/umidjonaska/Telegram-AI-Filtering-Engine/actions/workflows/ci.yml/badge.svg)](https://github.com/umidjonaska/Telegram-AI-Filtering-Engine/actions/workflows/ci.yml)

A personal Telegram assistant that watches all your groups and channels, uses an LLM to decide which
messages actually matter (e.g. job offers, freelance gigs, backend/IT vacancies) and forwards only those
to one place — with source, author, timestamp and a link back to the original message.

Built because job posts get lost in dozens of noisy Telegram groups.

## How it works

```
Telegram (Telethon, user account)
   │  new message / last 24h of history
   ▼
dedup (chat_id, msg_id)  ──seen──▶ skip
   │
   ▼
keyword pre-filter (optional, saves API calls)
   │
   ▼
text hash cache  ──already classified / forwarded──▶ skip
   │
   ▼
LLM classifier (Hugging Face router, OpenAI-compatible API)
   │  YES
   ▼
forward to target chat (Saved Messages, @channel, chat id)
```

## Features

- **Async end to end** — Telethon + `httpx.AsyncClient`, the LLM call never blocks the event loop;
  concurrency is bounded with a semaphore.
- **History catch-up** — on start, scans the last `HISTORY_HOURS` of every chat and stops as soon as it
  reaches older messages (no full-history downloads).
- **Persistent deduplication (SQLite)** — messages are never processed twice, even across restarts.
  The same vacancy cross-posted in 10 groups is classified and forwarded **once**.
- **Resilient API calls** — retries with exponential backoff on `429` / `5xx`, fails fast on auth errors.
- **Prompt-injection hardening** — message text is wrapped in tags, the model is told to treat it as data,
  and input length is capped.
- **Configurable without code changes** — topics, model, keywords, ignored chats via `.env`.
- **Tested** — unit tests for storage and the classifier (mocked HTTP), linted with ruff, CI on GitHub Actions.

## Quick start

```bash
git clone https://github.com/umidjonaska/Telegram-AI-Filtering-Engine.git
cd Telegram-AI-Filtering-Engine
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                               # fill in your credentials
python app.py
```

On first run Telethon asks for your phone number and login code and creates a local `*.session` file.

> ⚠️ The `.session` file grants full access to your Telegram account. Never commit or share it —
> it is excluded via `.gitignore`.

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `API_ID`, `API_HASH` | ✅ | — | From [my.telegram.org](https://my.telegram.org) |
| `HF_ACCESS_TOKEN` | ✅ | — | [Hugging Face token](https://huggingface.co/settings/tokens) |
| `TELEGRAM_TARGET` | ✅ | — | Where to forward: `me`, `@username` or chat id |
| `FILTER_TOPICS` | | jobs, freelance, IT, backend, jobs in Germany | What counts as "important" |
| `HF_MODEL` | | `mistralai/Mistral-7B-Instruct-v0.2` | Any chat model on the HF router |
| `PREFILTER_KEYWORDS` | | *(empty = off)* | Comma-separated; only matching messages reach the LLM |
| `HISTORY_HOURS` | | `24` | How far back to scan on start |
| `IGNORED_CHATS` | | — | Comma-separated usernames / ids |
| `INCLUDE_PRIVATE` | | `false` | Also scan private chats |
| `AI_CONCURRENCY` | | `3` | Parallel LLM requests |

See [.env.example](.env.example) for the full list.

## Development

```bash
pip install -r requirements-dev.txt
ruff check .
pytest
```

## Project structure

```
app.py          Telegram client, history scan, live listener, forwarding
ai_filter.py    LLM classifier: prompt, retries, pre-filter
storage.py      SQLite: seen messages, classification cache
config.py       .env loading and validation
tests/          pytest suite (HTTP mocked, no network needed)
```

## Roadmap

- Structured LLM output (category, salary, location, remote) instead of YES/NO
- Bot commands in the target chat: `/stats`, `/pause`, `/topics`
- 👍/👎 feedback on forwarded messages to tune the prompt
- Docker image
