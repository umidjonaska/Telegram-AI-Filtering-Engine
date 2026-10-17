import asyncio
import logging
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from telethon import TelegramClient, events
from telethon.tl.types import Channel

from ai_filter import AIFilter
from config import (
    API_HASH,
    API_ID,
    DB_PATH,
    HISTORY_HOURS,
    IGNORED_CHATS,
    INCLUDE_PRIVATE,
    LOG_LEVEL,
    SESSION_NAME,
    TELEGRAM_TARGET,
)
from storage import Storage, text_hash

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logging.getLogger("telethon").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("app")

TG_MAX_LEN = 4096

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
storage = Storage(DB_PATH)
ai = AIFilter()

target_id: int | None = None
ignored_ids: set[int] = set()
# Bir xil matn parallel ikki marta tekshirilmasligi uchun
text_locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)


def should_watch(chat_id: int, is_private: bool) -> bool:
    if chat_id == target_id or chat_id in ignored_ids:
        return False
    return INCLUDE_PRIVATE or not is_private


def message_link(chat, msg_id: int) -> str | None:
    username = getattr(chat, "username", None)
    if username:
        return f"https://t.me/{username}/{msg_id}"
    if isinstance(chat, Channel):
        return f"https://t.me/c/{chat.id}/{msg_id}"
    return None


async def format_message(msg, text: str) -> str:
    sender = await msg.get_sender()
    sender_name = None
    if sender is not None:
        username = getattr(sender, "username", None)
        sender_name = f"@{username}" if username else (
            " ".join(filter(None, [getattr(sender, "first_name", None), getattr(sender, "last_name", None)]))
            or getattr(sender, "title", None)
        )

    chat = await msg.get_chat()
    chat_name = getattr(chat, "title", None) or getattr(chat, "username", None) or "Private chat"
    link = message_link(chat, msg.id)

    header = (
        "🔥 Muhim xabar:\n\n"
        f"📌 Guruh/Kanal: {chat_name}\n"
        f"👤 Kim yozdi: {sender_name or 'Nomaʼlum'}\n"
        f"⏰ Jo'natilgan vaqt: {msg.date.astimezone().strftime('%Y-%m-%d %H:%M:%S')}\n"
        + (f"🔗 Havola: {link}\n" if link else "")
        + "\n"
    )
    room = TG_MAX_LEN - len(header)
    if len(text) > room:
        text = text[: room - 1] + "…"
    return header + text


async def process_message(msg):
    """Xabarni tekshiradi va muhim bo'lsa target chatga yuboradi"""
    if not storage.mark_seen(msg.chat_id, msg.id):
        return

    text = msg.raw_text
    if not text or not ai.passes_prefilter(text):
        return

    h = text_hash(text)
    try:
        async with text_locks[h]:
            verdict = storage.get_verdict(h)
            if verdict is None:
                important = await ai.is_important(text)
                if important is None:
                    return
                storage.save_verdict(h, important)
            else:
                important, forwarded = verdict
                if forwarded:
                    log.debug("Takroriy e'lon o'tkazib yuborildi: %s/%s", msg.chat_id, msg.id)
                    return

            if important:
                await client.send_message(
                    target_id, await format_message(msg, text), parse_mode=None, link_preview=False
                )
                storage.mark_forwarded(h)
                log.info("Yuborildi: chat=%s msg=%s", msg.chat_id, msg.id)
    except Exception:
        log.exception("Xabarni qayta ishlashda xato: chat=%s msg=%s", msg.chat_id, msg.id)
    finally:
        lock = text_locks.get(h)
        if lock is not None and not lock.locked() and not getattr(lock, "_waiters", None):
            text_locks.pop(h, None)


async def scan_history():
    """Oxirgi HISTORY_HOURS soatlik xabarlarni tekshiradi"""
    since = datetime.now(UTC) - timedelta(hours=HISTORY_HOURS)
    total = 0
    async for dialog in client.iter_dialogs():
        if not should_watch(dialog.id, dialog.is_user):
            continue
        if dialog.date and dialog.date < since:
            continue  # bu chatda oxirgi vaqtda xabar yo'q

        tasks = []
        # iter_messages yangidan eskiga qarab beradi — eski xabarga yetganda to'xtaymiz
        async for msg in client.iter_messages(dialog.entity):
            if msg.date < since:
                break
            tasks.append(process_message(msg))
        if tasks:
            await asyncio.gather(*tasks)
            total += len(tasks)
    log.info("Tarix tekshiruvi tugadi: %s ta xabar ko'rildi", total)


@client.on(events.NewMessage(incoming=True))
async def handler(event):
    if should_watch(event.chat_id, event.is_private):
        await process_message(event.message)


async def main():
    global target_id

    await client.start()
    target_id = await client.get_peer_id(TELEGRAM_TARGET)
    for chat in IGNORED_CHATS:
        try:
            ignored_ids.add(await client.get_peer_id(int(chat) if chat.lstrip("-").isdigit() else chat))
        except Exception as e:
            log.warning("IGNORED_CHATS dagi %r topilmadi: %s", chat, e)

    storage.cleanup()
    await client.send_message(target_id, "🚀 Telegram AI filter listener ishga tushdi!")
    log.info("Telegram listener ishlayapti...")

    history_task = asyncio.create_task(scan_history())
    try:
        await client.run_until_disconnected()
    finally:
        history_task.cancel()
        await ai.close()
        storage.close()


if __name__ == "__main__":
    try:
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        log.info("To'xtatildi")
