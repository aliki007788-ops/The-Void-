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
from aiogram.types import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from PIL import Image
from dotenv import load_dotenv
import uvicorn

# بارگذاری متغیرها
load_dotenv()

# --- تنظیمات اصلی ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_API_TOKEN")
# آدرس اپلیکیشن شما در Render
BASE_URL = "https://the-void-1.onrender.com" 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# ایجاد پوشه‌های مورد نیاز و اتصال فایل‌های استاتیک
os.makedirs("static/outputs", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- راه‌اندازی دیتابیس ---
def init_db():
    conn = sqlite3.connect("void_core.db")
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0)")
    conn.execute("CREATE TABLE IF NOT EXISTS collection (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, dna TEXT, path TEXT, date TEXT)")
    conn.commit()
    conn.close()

init_db()

# --- بخش ربات تلگرام (هندلر پیام خوش‌آمدگویی) ---
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
        "This is not merely a journey. This is the beginning of your everlasting reign.\n\n"
        "<b>The Void bows to no one... except you.</b>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌌 ENTER THE VOID", web_app=WebAppInfo(url=BASE_URL))],
        [InlineKeyboardButton(text="👑 Join Channel", url="https://t.me/your_channel")]
    ])
    
    await message.answer(welcome_text, reply_markup=kb, parse_mode=ParseMode.HTML)

# --- تابع تولید گواهی با هوش مصنوعی ---
async def generate_ai_art(user_id, burden):
    prompt = f"luxurious ancient golden decree certificate, void theme, cosmic background, sacred symbols, high detail, 8k"
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
        print(f"AI/HF Error: {e}")
        # تصویر رزرو در صورت خطا (یک تصویر مشکی شیک)
        image = Image.new('RGB', (1000, 1300), color='#050505')

    dna = hashlib.md5(f"{user_id}{datetime.now()}".encode()).hexdigest()[:10].upper()
    filename = f"{user_id}_{dna}.png"
    save_path = f"static/outputs/{filename}"
    image.save(save_path)
    
    # ذخیره در دیتابیس برای گالری
    conn = sqlite3.connect("void_core.db")
    conn.execute("INSERT INTO collection (user_id, dna, path, date) VALUES (?, ?, ?, ?)",
                 (user_id, dna, save_path, datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()
    
    return filename, dna

# --- مسیرهای API برای فرانت‌اِند (HTML) ---

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/mint")
async def api_mint(request: Request):
    data = await request.json()
    uid = data.get("u")
    burden = data.get("b")
    
    # تولید تصویر
    filename, dna = await generate_ai_art(uid, burden)
    img_url = f"{BASE_URL}/static/outputs/{filename}"
    
    # ارسال به تلگرام کاربر
    try:
        await bot.send_photo(
            uid, 
            types.FSInputFile(f"static/outputs/{filename}"),
            caption=f"🔱 <b>ASCENSION SUCCESSFUL</b>\n\nYour burden <i>'{burden}'</i> has been consumed.\n\nDNA: <code>{dna}</code>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        print(f"Telegram Send Error: {e}")

    return {"status": "success", "dna": dna, "url": img_url}

@app.get("/api/gallery/{user_id}")
async def api_gallery(user_id: int):
    conn = sqlite3.connect("void_core.db")
    cursor = conn.cursor()
    cursor.execute("SELECT dna, path FROM collection WHERE user_id = ? ORDER BY id DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    images = [{"dna": r[0], "url": f"{BASE_URL}/{r[1]}"} for r in rows]
    return {"images": images}

# --- هندلر وبهوک تلگرام (رفع خطای ۴۰۴) ---
@app.post("/webhook")
async def telegram_webhook(request: Request):
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return Response(status_code=200)

@app.on_event("startup")
async def on_startup():
    # تنظیم وبهوک به محض بالا آمدن سرور
    webhook_url = f"{BASE_URL}/webhook"
    await bot.set_webhook(webhook_url, drop_pending_updates=True)
    print(f"🚀 Webhook set to: {webhook_url}")

if __name__ == "__main__":
    # رندر پورت را از متغیر محیطی می‌گیرد
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
