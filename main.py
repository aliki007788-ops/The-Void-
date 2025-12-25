import os
import sqlite3
import hashlib
import requests
import io
import asyncio
from datetime import datetime
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
import uvicorn

load_dotenv()

# --- تنظیمات متغیرهای محیطی ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_API_TOKEN")
# آدرس دقیق اپلیکیشن شما در رندر
BASE_URL = "https://the-void-1.onrender.com" 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# ایجاد پوشه‌های مورد نیاز
os.makedirs("static/outputs", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- دیتابیس ---
def init_db():
    conn = sqlite3.connect("void_core.db")
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, refs INTEGER DEFAULT 0)")
    conn.commit()
    conn.close()

init_db()

# --- بخش ربات تلگرام (پیام خوش‌آمدگویی حماسی) ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    welcome_text = (
        "🌌 <b>Emperor of the Eternal Void, the cosmos summons you...</b> 👑\n\n"
        "In the infinite depths of darkness, where stars have long faded and time itself has surrendered,\n"
        "<b>The Void</b> awaits your arrival — only the chosen few dare to ascend to immortality.\n\n"
        "Name your burden.\n"
        "Burn it in golden flames.\n"
        "And rise as the sovereign ruler of the eternal realm.\n\n"
        "Each ascension grants you a unique, forever-irreplaceable certificate — forged in celestial gold, "
        "sealed with the light of dead stars, bearing one of 30 rare imperial styles, and eternally tied to your soul.\n\n"
        "Only the boldest spirits step forward.\n"
        "Are you one of them?\n\n"
        "🔱 <b>Enter The Void now and claim your eternal crown.</b>\n\n"
        "This is not merely a journey.\n"
        "This is the beginning of your everlasting reign.\n\n"
        "<b>The Void bows to no one... except you.</b>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌌 ENTER THE VOID", web_app=WebAppInfo(url=BASE_URL))],
        [InlineKeyboardButton(text="👥 My Referral Link", callback_data="ref")]
    ])
    
    await message.answer(welcome_text, reply_markup=kb, parse_mode=ParseMode.HTML)

# --- تولید گواهی با هوش مصنوعی ---
async def generate_ai_certificate(user_id, burden, level="Eternal"):
    prompt = f"mythical ancient gold certificate, {level} style, void background, sacred geometry, highly detailed, 8k"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    try:
        # فراخوانی مدل Stable Diffusion
        response = requests.post(
            "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5",
            headers=headers,
            json={"inputs": prompt},
            timeout=40
        )
        image = Image.open(io.BytesIO(response.content))
    except Exception as e:
        print(f"AI Error: {e}")
        # تصویر رزرو در صورت خطا
        image = Image.new('RGB', (1000, 1300), color='#050505')

    draw = ImageDraw.Draw(image)
    dna = hashlib.sha256(f"{user_id}{datetime.now()}".encode()).hexdigest()[:10].upper()
    
    # (در اینجا می‌توانید کدهای رسم متن روی تصویر را اضافه کنید)
    
    path = f"static/outputs/{dna}.png"
    image.save(path)
    return path, dna

# --- هندلرهای وب‌سرویس (اتصال به HTML) ---

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/create_stars_invoice")
async def create_invoice(request: Request):
    data = await request.json()
    uid = data.get("u")
    burden = data.get("b")
    plan = data.get("type", "eternal")
    
    # اگر رایگان بود بلافاصله عکس را بساز و بفرست
    if plan == "eternal":
        path, dna = await generate_ai_certificate(uid, burden)
        await bot.send_photo(
            uid, 
            types.FSInputFile(path), 
            caption=f"🔱 **ASCENSION SUCCESSFUL**\n\nYour burden '{burden}' has been consumed by the void.\n\nDNA: `{dna}`",
            parse_mode="Markdown"
        )
        return {"status": "success", "free": True}
    
    # (بخش پرداخت ستاره برای پلن‌های پولی در اینجا قرار می‌گیرد)
    return {"status": "pending"}

# --- مسیر اصلی Webhook تلگرام ---
@app.post("/webhook")
async def telegram_webhook(request: Request):
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return Response(status_code=200)

@app.on_event("startup")
async def on_startup():
    # تنظیم وبهوک برای جلوگیری از خطای 404
    await bot.set_webhook(f"{BASE_URL}/webhook", drop_pending_updates=True)
    print(f"🚀 Webhook set to {BASE_URL}/webhook")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
