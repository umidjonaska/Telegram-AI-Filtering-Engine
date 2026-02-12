from telethon import TelegramClient, events
from config import API_ID, API_HASH, TELEGRAM_TARGET
from ai_filter import is_important
from datetime import datetime, timedelta, timezone

client = TelegramClient("session", API_ID, API_HASH)

sent_message_ids = set()

async def send_if_new(msg):
    """Xabar hali forward qilinmagan bo'lsa forward qiladi"""
    if msg.id in sent_message_ids:
        return
    sent_message_ids.add(msg.id)

    text = msg.raw_text
    if not text:
        return

    try:
        if is_important(text):

            sender = await msg.get_sender()
            sender_name = getattr(sender, 'username', None) or getattr(sender, 'first_name', 'Noma\'lum')

            chat = await msg.get_chat()
            chat_name = getattr(chat, 'title', None) or getattr(chat, 'username', None) or 'Private chat'

            timestamp = msg.date.strftime("%Y-%m-%d %H:%M:%S")

            await client.send_message(
                TELEGRAM_TARGET,
                f"🔥 Muhim xabar:\n\n"
                f"📌 Guruh/Kanal: {chat_name}\n"
                f"👤 Kim yozdi: {sender_name}\n"
                f"⏰ Jo'natilgan vaqt: {timestamp}\n\n"
                f"{text}"
            )
    except Exception as e:
        print("Error:", e)

async def get_recent_messages(chat, hours=24):
    """Oxirgi 24 soatlik xabarlarni oladi"""
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    history = await client.get_messages(chat, limit=None)
    recent = [msg for msg in history if msg.date >= since]
    return recent

async def main():

    dialogs = await client.get_dialogs()
    for dialog in dialogs:
        recent_msgs = await get_recent_messages(dialog.entity, hours=24)
        for msg in recent_msgs:
            await send_if_new(msg)

async def start_listener():
    await client.start()

    await client.send_message(TELEGRAM_TARGET, "🚀 Telegram AI filter listener ishga tushdi!")
    print("Telegram listener ishlayapti...")
    await main()

client.loop.run_until_complete(start_listener())

@client.on(events.NewMessage)
async def handler(event):
    chat = await event.get_chat()

    if chat.id == TELEGRAM_TARGET:
        return

    await send_if_new(event.message)

client.run_until_disconnected()
