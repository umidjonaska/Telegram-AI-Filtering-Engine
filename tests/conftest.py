import os
import sys
from pathlib import Path

# config.py majburiy o'zgaruvchilarni talab qiladi — testlar uchun soxta qiymatlar
os.environ.update(
    {
        "API_ID": "12345",
        "API_HASH": "test_hash",
        "HF_ACCESS_TOKEN": "hf_test",
        "TELEGRAM_TARGET": "me",
        "PREFILTER_KEYWORDS": "ish,python,job",
        "MIN_TEXT_CHARS": "10",
    }
)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
