import asyncio
import os
from telegram import Bot
from telegram.error import RetryAfter
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=BOT_TOKEN)

async def send_alert(job):
    message = f"""
🆕 New Job Found!

🏢 Company: {job['company']}
💼 Title: {job['title']}
🔗 Apply: {job['url']}
"""

    while True:
        try:
            await bot.send_message(
                chat_id=CHAT_ID,
                text=message
            )
            return  # success → exit function

        except RetryAfter as e:
            wait_time = e.retry_after
            print(f"⚠️ Telegram rate limit hit. Waiting {wait_time} seconds...")
            await asyncio.sleep(wait_time)

async def notify(job):
    await send_alert(job)