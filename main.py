import os
import json
import random
import sqlite3
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import LabeledPrice, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from cert_gen import create_certificate
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# --- دیتابیس ساده برای ذخیره رفرال‌ها و تاریخچه ---
def init_db():
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, referrals INTEGER DEFAULT 0, invited_by INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS gallery 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, dna TEXT, path TEXT, level TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# --- متدهای کمکی ---
def get_user_stats(user_id):
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    c.execute("SELECT referrals FROM users WHERE user_id = ?", (user_id,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else 0

# --- API برای فرانت‌اِند ---
@app.get("/api/init/{user_id}")
async def init_user(user_id: int):
    ref_count = get_user_stats(user_id)
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    c.execute("SELECT path, level, dna FROM gallery ORDER BY id DESC LIMIT 60")
    top_60 = [{"path": r[0], "level": r[1], "dna": r[2]} for r in c.fetchall()]
    conn.close()
    return {"ref_count": ref_count, "top_60": top_60}

@app.post("/api/create_invoice")
async def create_invoice(data: dict):
    uid = data.get('u')
    level = data.get('level', 'Eternal')
    is_luck = data.get('is_luck', False)
    
    # منطق قیمت‌گذاری
    price = 30 if is_luck else 70
    if level == "Legendary": price = 150
    
    # اگر ۶ نفر را دعوت کرده باشد رایگان است
    ref_count = get_user_stats(uid)
    if ref_count >= 6:
        # کسر ۶ رفرال پس از استفاده
        return {"free": True}

    link = await bot.create_invoice_link(
        title=f"ASCENSION: {level.upper()}",
        description="Fading into the void...",
        payload=f"{uid}:{data['b']}:{level}",
        provider_token="", # برای Telegram Stars خالی بماند
        currency="XTR",
        prices=[LabeledPrice(label="Offering", amount=price)]
    )
    return {"url": link}

# --- هندلر تلگرام برای رفرال ---
@dp.message(F.text.startswith("/start"))
async def cmd_start(message: types.Message):
    args = message.text.split()
    uid = message.from_user.id
    
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (uid,))
    
    if len(args) > 1 and args[1].isdigit():
        inviter_id = int(args[1])
        if inviter_id != uid:
            c.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id = ?", (inviter_id,))
    conn.commit()
    conn.close()

    markup = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="ENTER THE VOID", web_app=WebAppInfo(url=os.getenv("WEBAPP_URL")))
    ]])
    await message.answer("🔱 WELCOME TO THE VOID\nSacrifice your burden to become eternal.", reply_markup=markup)

app.mount("/", StaticFiles(directory=".", html=True), name="static")
