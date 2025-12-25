import os
import json
import sqlite3
import asyncio
import requests
import io
import hashlib
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, Update
from aiogram.enums import ParseMode
from dotenv import load_dotenv
import uvicorn

load_dotenv()

# --- Configurations ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_API_TOKEN")
RENDER_URL = "https://the-void-1.onrender.com" # آدرس دقیق شما
API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# Mount Static Files
if not os.path.exists("static/outputs"):
    os.makedirs("static/outputs", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Database Init
def init_db():
    conn = sqlite3.connect("void_core.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, refs INTEGER DEFAULT 0)")
    conn.commit()
    conn.close()

init_db()

# --- Telegram Bot Logic ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    welcome_text = (
        "🌌 <b>Emperor of the Eternal Void, the cosmos summons you...</b> 👑\n\n"
        "In the infinite depths of darkness, <b>The Void</b> awaits.\n"
        "Name your burden, burn it in golden flames, and rise.\n\n"
        "🔱 <b>Enter The Void now and claim your eternal crown.</b>"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌌 ENTER THE VOID", web_app=WebAppInfo(url=RENDER_URL))]
    ])
    await message.answer(welcome_text, reply_markup=kb, parse_mode=ParseMode.HTML)

# --- AI Certificate Generator ---
async def generate_cert(user_id, burden, level):
    prompt = f"luxurious golden certificate, void background, sacred geometry, {level} style, high detail"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt}, timeout=30)
        image = Image.open(io.BytesIO(response.content))
    except:
        image = Image.new('RGB', (800, 1000), color='#050505')

    draw = ImageDraw.Draw(image)
    dna = hashlib.md5(f"{user_id}{datetime.now()}".encode()).hexdigest()[:8].upper()
    # Drawing logic...
    path = f"static/outputs/{dna}.png"
    image.save(path)
    return path, dna

# --- FastAPI Endpoints ---
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/create_stars_invoice")
async def create_invoice(request: Request):
    data = await request.json()
    uid = data.get("u")
    plan = data.get("type")
    prices = {"eternal": 0, "divine": 150, "celestial": 299, "legendary": 499}
    
    if prices.get(plan) == 0:
        path, dna = await generate_cert(uid, data.get("b"), "Eternal")
        await bot.send_photo(uid, types.FSInputFile(path), caption=f"🌌 DNA: {dna}")
        return {"free": True}

    link = await bot.create_invoice_link(
        title="VOID ASCENSION",
        description=f"Level: {plan}",
        payload=f"{uid}:{data.get('b')}:{plan}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Fee", amount=prices[plan])]
    )
    return {"url": link}

# --- CRITICAL: Webhook Handler ---
@app.post("/webhook")
async def telegram_webhook(request: Request):
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return Response(status_code=200)

@app.on_event("startup")
async def on_startup():
    # تنظیم وبهوک برای رفع خطای 404 در لاگ رندر
    webhook_url = f"{RENDER_URL}/webhook"
    await bot.set_webhook(webhook_url, drop_pending_updates=True)
    print(f"🚀 Webhook set to: {webhook_url}")

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
