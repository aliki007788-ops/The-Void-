import os
import random
import sqlite3
import base64
import tempfile
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import LabeledPrice, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from cert_gen import create_certificate 
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# --- قیمت‌های جدید بر اساس درخواست شما ---
PRICES = {
    "Vagabond": 139,
    "Imperial": 299,
    "Eternal": 499,
    "Luck": 249
}

def init_db():
    conn = sqlite3.connect("void.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, refs INTEGER DEFAULT 0)")
    c.execute("CREATE TABLE IF NOT EXISTS hall (path TEXT, dna TEXT, level TEXT)")
    conn.commit()
    conn.close()

init_db()

def get_luck_level():
    chance = random.randint(1, 100)
    if chance <= 60: return "Eternal"     # ۶۰٪ سطح پایه
    if chance <= 90: return "Divine"      # ۳۰٪ سطح بعدی
    if chance <= 99: return "Celestial"   # ۹٪ سطح حرفه‌ای
    return "Legendary"                    # ۱٪ سطح فوق حرفه‌ای

@app.post("/api/create_invoice")
async def create_invoice(data: dict):
    uid = data.get('u')
    burden = data.get('b')
    level = data.get('level')
    photo_b64 = data.get('p')

    # قیمت و لول نهایی
    final_level = level
    if level == "Luck":
        final_level = get_luck_level()
        price = PRICES["Luck"]
    else:
        price = PRICES.get(level, 139)

    # چک کردن رفرال ۶ تایی
    conn = sqlite3.connect("void.db")
    c = conn.cursor()
    c.execute("SELECT refs FROM users WHERE id = ?", (uid,))
    refs = c.fetchone()[0] if c.fetchone() else 0
    if refs >= 6:
        c.execute("UPDATE users SET refs = 0 WHERE id = ?", (uid,))
        conn.commit()
        conn.close()
        return {"free": True, "level": final_level}
    conn.close()

    temp_path = "none"
    if photo_b64:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(base64.b64decode(photo_b64.split(",")[1]))
            temp_path = tmp.name

    payload = f"{uid}:{burden}:{final_level}:{temp_path}"
    link = await bot.create_invoice_link(
        title=f"VOID: {final_level.upper()}",
        description=f"Sacrifice: {burden[:50]}",
        payload=payload,
        currency="XTR",
        prices=[LabeledPrice(label="Offering", amount=price)]
    )
    return {"url": link}

# هندلرهای بات برای استارت و پرداخت در اینجا قرار می‌گیرند (مشابه کدهای قبلی)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
