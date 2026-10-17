import os
import sys

from dotenv import load_dotenv

load_dotenv()


def _required(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        sys.exit(f"Xato: .env faylida {name} berilmagan (namuna uchun .env.example ga qarang)")
    return value


def _list(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# --- Majburiy sozlamalar ---
API_ID = int(_required("API_ID"))
API_HASH = _required("API_HASH")
HF_ACCESS_TOKEN = _required("HF_ACCESS_TOKEN")
# "me" (Saved Messages), @username yoki raqamli chat id
TELEGRAM_TARGET = _required("TELEGRAM_TARGET")
if TELEGRAM_TARGET.lstrip("-").isdigit():
    TELEGRAM_TARGET = int(TELEGRAM_TARGET)

# --- AI sozlamalari ---
HF_MODEL = os.getenv("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
HF_API_URL = os.getenv("HF_API_URL", "https://router.huggingface.co/v1/chat/completions")
FILTER_TOPICS = os.getenv(
    "FILTER_TOPICS",
    "ish taklifi, vakansiya, freelance buyurtma, IT, backend dasturlash yoki Germaniyada ish",
)
# Bo'sh bo'lmasa: xabarda shu so'zlardan biri bo'lmasa AI ga yuborilmaydi (API tejaladi)
PREFILTER_KEYWORDS = [k.lower() for k in _list("PREFILTER_KEYWORDS")]
MAX_TEXT_CHARS = int(os.getenv("MAX_TEXT_CHARS", "2000"))
MIN_TEXT_CHARS = int(os.getenv("MIN_TEXT_CHARS", "20"))
AI_CONCURRENCY = int(os.getenv("AI_CONCURRENCY", "3"))

# --- Telegram sozlamalari ---
SESSION_NAME = os.getenv("SESSION_NAME", "session")
HISTORY_HOURS = float(os.getenv("HISTORY_HOURS", "24"))
# Kuzatilmaydigan chatlar: @username yoki id, vergul bilan
IGNORED_CHATS = _list("IGNORED_CHATS")
# Shaxsiy (private) chatlarni ham tekshirish kerakmi
INCLUDE_PRIVATE = os.getenv("INCLUDE_PRIVATE", "false").lower() in ("1", "true", "yes")

DB_PATH = os.getenv("DB_PATH", "filter.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
