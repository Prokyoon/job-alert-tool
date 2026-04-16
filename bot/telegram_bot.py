import asyncio
import os
from telegram import Bot
from dotenv import load_dotenv
 
load_dotenv()
 
async def send_alert(job: dict):
    bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    message = (
        f"New job found\n\n"
        f"Company: {job['company']}\n"
        f"Role: {job['title']}\n"
        f"Location: {job['location']}\n"
        f"Link: {job['url']}"
    )
    await bot.send_message(chat_id=chat_id, text=message)
 
def notify(job: dict):
    asyncio.run(send_alert(job))