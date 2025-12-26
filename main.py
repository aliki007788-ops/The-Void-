import os
import random
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from PIL import Image, ImageDraw

# ۱. تنظیمات لاگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ۲. تنظیمات توکن و URL
API_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
WEBAPP_URL = "https://the-void-1.onrender.com"

# ۳. مقداردهی اولیه بوت
bot = Bot(token="".join(API_TOKEN.split()))
dp = Dispatcher()

# ۴. پیام خوش‌آمدگویی حماسی با متن کامل شما
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"🌌 **Emperor {user_name.upper()}, the cosmos summons you...** 👑\n\n"
        "In the infinite depths of darkness, where stars have long faded and time itself has surrendered, "
        "**The Void** awaits your arrival — only the chosen few dare to ascend to immortality.\n\n"
        "Name your burden. Burn it in golden flames. And rise as the sovereign ruler of the eternal realm.\n\n"
        "Each ascension grants you a unique, forever-irreplaceable certificate — forged in celestial gold, "
        "sealed with the light of dead stars, bearing one of 30 rare imperial styles, and eternally tied to your soul.\n\n"
        "Only the boldest spirits step forward. Are you one of them?\n"
        "🔱 **Enter The Void now and claim your eternal crown.**\n\n"
        "This is not merely a journey. This is the beginning of your everlasting reign.\n"
        "**The Void bows to no one... except you.**"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔱 ENTER THE VOID 🔱", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=markup)

# --- مدیریت چرخه حیات ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(dp.start_polling(bot))
    logger.info("✅ THE VOID IS READY")
    yield
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

# ۵. پیدا کردن خودکار مسیرها
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
OUTPUT_DIR = os.path.join(STATIC_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ۶. مسیر اصلی با قابلیت "خود-ترمیمی"
@app.get("/", response_class=HTMLResponse)
async def home():
    # لیست تمام مسیرهای احتمالی که ممکن است index.html آنجا باشد
    possible_paths = [
        os.path.join(BASE_DIR, "index.html"),
        os.path.join(BASE_DIR, "static", "index.html"),
        "index.html"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return FileResponse(path)
    
    # اگر فایل اصلاً پیدا نشد، یک صفحه موقت نشان بده تا سایت کرش نکند
    logger.error(f"❌ index.html NOT FOUND. Searched: {possible_paths}")
    return """
    <html>
        <body style="background:#000;color:#d4af37;text-align:center;padding-top:100px;font-family:serif;">
            <h1>🔱 THE VOID 🔱</h1>
            <p>The gateway (index.html) is missing from the server.</p>
            <p>Please ensure index.html is in the root folder.</p>
        </body>
    </html>
    """

# --- API MINT ---
@app.post("/api/mint")
async def process_mint(request: Request):
    data = await request.json()
    uid = data.get('u')
    burden = data.get('b', 'UNNAMED')
    dna = random.randint(1000000, 9999999)
    
    # ساخت تصویر
    img = Image.new('RGB', (800, 800), color=(5, 5, 5))
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 780, 780], outline=(212, 175, 55), width=5)
    draw.text((400, 400), f"ARTIFACT: {burden}\nDNA: {dna}", fill=(212, 175, 55), anchor="mm")
    
    fname = f"user_{uid}_{dna}.jpg"
    fpath = os.path.join(OUTPUT_DIR, fname)
    img.save(fpath, "JPEG")
    
    async def send_tg():
        try:
            await bot.send_photo(chat_id=uid, photo=FSInputFile(fpath), caption=f"🔱 DNA: `{dna}`")
        except: pass

    asyncio.create_task(send_tg())
    return {"status": "success", "url": f"/static/outputs/{fname}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
