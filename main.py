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
bot = Bot(token=os.getenv("BOT_TOKEN"))
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

    # دکمه ورود به وب‌اپ (آدرس دامنه خود را جایگزین کنید)
    web_app_url = "https://your-domain.com" # <--- آدرس سایت خود را اینجا بگذارید
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔱 ENTER THE VOID", web_app=WebAppInfo(url=web_app_url))],
        [InlineKeyboardButton(text="👥 دعوت از برادران (Referral)", callback_data="ref_link")]
    ])

    await message.answer(
        "The Void calls. Will you answer?\nConsume your burden. Ascend to the Void.\n\n"
        "🔱 ورود به خلأ و دریافت گواهینامه ابدی:",
        reply_markup=kb
    )

@dp.callback_query(F.data == "ref_link")
async def send_ref_link(callback: types.CallbackQuery):
    ref_link = f"https://t.me/{(await bot.get_me()).username}?start={callback.from_user.id}"
    await callback.message.answer(f"لینک دعوت شما:\n`{ref_link}`\n\nبا دعوت ۶ نفر، صعود شما رایگان خواهد بود.", parse_mode="Markdown")

# --- تنظیمات وب‌سرور (FastAPI) ---
# این بخش برای نمایش فایل‌های استاتیک و حل خطای Not Found است
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

# --- بخش نهایی برای اجرای همزمان بات و سرور ---
import asyncio

async def main():
    # شروع پولینگ تلگرام در پس‌زمینه
    asyncio.create_task(dp.start_polling(bot))
    # اجرای سرور FastAPI
    import uvicorn
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
