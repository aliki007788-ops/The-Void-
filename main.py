import os
import sqlite3
import hashlib
import requests
import io
from datetime import datetime
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
import uvicorn

load_dotenv()

# --- تنطیمات ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_API_TOKEN")
BASE_URL = "https://the-void-1.onrender.com"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# ایجاد پوشه برای ذخیره عکس‌ها
os.makedirs("static/outputs", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- دیتابیس ساده ---
def init_db():
    conn = sqlite3.connect("void.db")
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

init_db()

# --- هندلر تلگرام ---
@dp.message(CommandStart())
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌌 ENTER THE VOID", web_app=WebAppInfo(url=BASE_URL))]
    ])
    await message.answer("🌌 Welcome, Emperor. Your ascension awaits...", reply_markup=kb)

# --- مسیر اصلی Webhook (رفع خطای ۴۰۴) ---
@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        dict_update = await request.json()
        update = Update.model_validate(dict_update, context={"bot": bot})
        await dp.feed_update(bot, update)
        return Response(status_code=200)
    except Exception as e:
        print(f"Error handling update: {e}")
        return Response(status_code=400)

# --- تولید عکس با هوش مصنوعی ---
async def generate_void_art(user_id, burden):
    # این بخش به توکن HuggingFace نیاز دارد
    prompt = f"mystical golden artifact in cosmic void, ethereal light, engraving '{burden}'"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    try:
        # فراخوانی مدل SD
        resp = requests.post("https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5", 
                             headers=headers, json={"inputs": prompt})
        img = Image.open(io.BytesIO(resp.content))
    except:
        # اگر هوش مصنوعی خطا داد، یک تصویر مشکی شیک بساز
        img = Image.new('RGB', (800, 1000), color='#050505')
    
    dna = hashlib.md5(f"{user_id}{datetime.now()}".encode()).hexdigest()[:8].upper()
    path = f"static/outputs/{dna}.png"
    img.save(path)
    return path, dna

# --- دریافت درخواست از وب‌اپ ---
@app.post("/create_stars_invoice")
async def process_request(request: Request):
    data = await request.json()
    user_id = data.get("u")
    burden = data.get("b")
    
    # برای تست رایگان:
    path, dna = await generate_void_art(user_id, burden)
    await bot.send_photo(user_id, types.FSInputFile(path), 
                         caption=f"🔱 **ASCENSION SUCCESSFUL**\n\nDNA: `{dna}`", 
                         parse_mode="Markdown")
    return {"status": "ok"}

# --- راه‌اندازی سرور و وبهوک ---
@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(f"{BASE_URL}/webhook", drop_pending_updates=True)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
