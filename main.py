import os
import json
import random
import sqlite3
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()

# --- تنظیمات ---
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env file!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
app = FastAPI()

# --- دیتابیس رفرال و کاربران ---
def init_db():
    conn = sqlite3.connect("void_core.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, refs INTEGER DEFAULT 0, referred_by INTEGER)")
    conn.commit()
    conn.close()

init_db()

# --- هندلر دستور استارت (Telegram Start Handler) ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    inviter_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    
    conn = sqlite3.connect("void_core.db")
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    user_exists = c.fetchone()
    
    if not user_exists:
        c.execute("INSERT INTO users (id, referred_by) VALUES (?, ?)", (user_id, inviter_id))
        if inviter_id:
            c.execute("UPDATE users SET refs = refs + 1 WHERE id = ?", (inviter_id,))
        conn.commit()
    conn.close()
    
    # === آدرس واقعی وب اپ The Void ===
    web_app_url = "https://the-void-1.onrender.com"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌌 ENTER THE VOID", web_app=WebAppInfo(url=web_app_url))],
        [InlineKeyboardButton(text="👥 دعوت از برادران (Referral)", callback_data="ref_link")]
    ])
    
    await message.answer(
        "<b>🌌 Emperor of the Eternal Void, the cosmos summons you...</b>\n\n"
        "In the infinite depths of darkness, where stars have long faded and time itself has surrendered,\n"
        "<b>The Void</b> awaits your arrival — only the chosen few dare to ascend to immortality.\n\n"
        "Name your burden.\n"
        "Burn it in golden flames.\n"
        "And rise as the sovereign ruler of the eternal realm.\n\n"
        "Each ascension grants you a unique, forever-irreplaceable certificate — forged in celestial gold, "
        "sealed with the light of dead stars, bearing one of 30 rare imperial styles, and eternally tied to your soul.\n\n"
        "Only the boldest spirits step forward.\n"
        "<b>Are you one of them?</b>\n\n"
        "🔱 <b>Enter The Void now and claim your eternal crown.</b>\n\n"
        "(Invite 6 worthy souls to join you, and your next ascension shall be granted free of charge — "
        "your referral link awaits below)\n\n"
        "This is not merely a journey.\n"
        "<b>This is the beginning of your everlasting reign.</b>\n\n"
        "<i>The Void bows to no one... except you.</i>",
        reply_markup=kb,
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "ref_link")
async def send_ref_link(callback: types.CallbackQuery):
    bot_username = (await bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={callback.from_user.id}"
    await callback.message.answer(
        f"🔗 <b>Referral Link:</b>\n\n"
        f"<code>{ref_link}</code>\n\n"
        f"Invite 6 worthy souls and your next ascension will be granted free of charge.",
        parse_mode="HTML"
    )

# --- تنظیمات وب‌سرور (FastAPI) ---
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>The Void awaits... (index.html not found)</h1>"

# --- بخش نهایی برای اجرای همزمان بات و سرور ---
import asyncio
import uvicorn

async def main():
    # شروع پولینگ تلگرام در پس‌زمینه
    asyncio.create_task(dp.start_polling(bot))
    # اجرای سرور FastAPI
    config = uvicorn.Config(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
