import os
import json
import random
import asyncio
import logging
import sqlite3
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
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

# --- URL وب اپ ---
WEBAPP_URL = "https://the-void-1.onrender.com"

# --- دیتابیس رفرال و کاربران ---
def init_db():
    conn = sqlite3.connect("void_core.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, refs INTEGER DEFAULT 0, referred_by INTEGER)")
    conn.commit()
    conn.close()

init_db()

# --- پیام خوش‌آمدگویی شاهانه و حماسی (انگلیسی) ---
WELCOME_MESSAGE = (
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
    "<i>The Void bows to no one... except you.</i>"
)

# --- هندلر دستور استارت ---
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
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌌 ENTER THE VOID", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="👥 دعوت از برادران (Referral)", callback_data="ref_link")]
    ])
    
    await message.answer(WELCOME_MESSAGE, parse_mode="HTML", reply_markup=kb)

@dp.callback_query(F.data == "ref_link")
async def send_ref_link(callback: types.CallbackQuery):
    bot_username = (await bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={callback.from_user.id}"
    await callback.message.answer(
        f"🔗 <b>لینک دعوت شما:</b>\n\n"
        f"<code>{ref_link}</code>\n\n"
        f"با دعوت ۶ نفر، صعود شما رایگان خواهد بود.",
        parse_mode="HTML"
    )

# --- تنظیمات وب‌سرور (FastAPI) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return "<h1>🌌 THE VOID</h1><p>index.html not found. Place your app file in /static folder.</p>"

# --- اجرای همزمان بات و سرور ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(dp.start_polling(bot))
    logging.info("🌌 THE VOID BOT & SERVER IS ALIVE")
    yield
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
