import os
import random
import asyncio
import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from PIL import Image, ImageDraw

# ۱. تنظیمات لاگ برای دیدن دقیق اتفاقات در کنسول رندر
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ۲. متغیرهای محیطی
# پیشنهاد: توکن را در پنل Render در بخش Environment Variables با نام BOT_TOKEN ست کنید
API_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
WEBAPP_URL = "https://the-void-1.onrender.com"

app = FastAPI()

# ۳. مقداردهی اولیه بدون چک کردن توکن در ابتدای فایل
bot = None
dp = Dispatcher()

# مدیریت مسیرها
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
OUTPUT_DIR = os.path.join(STATIC_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# --- تابع تولید آرتیفکت امپراطوری ---
def forge_artifact(text, dna, user_id):
    try:
        img = Image.new('RGB', (800, 800), color=(1, 1, 1))
        draw = ImageDraw.Draw(img)
        gold = (212, 175, 55)
        draw.rectangle([20, 20, 780, 780], outline=gold, width=4)
        content = f"THE VOID\n\nSOVEREIGN: {user_id}\nBURDEN: {text.upper()}\nDNA: {dna}"
        draw.text((400, 400), content, fill=gold, anchor="mm", align="center")
        filename = f"user_{user_id}_{dna}.jpg"
        filepath = os.path.join(OUTPUT_DIR, filename)
        img.save(filepath, "JPEG")
        return filepath, filename
    except Exception as e:
        logger.error(f"Image creation error: {e}")
        return None, None

# --- هندلر شروع ربات با متن حماسی ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"🌌 **Emperor {user_name.upper()}, the cosmos summons you...** 👑\n\n"
        "In the infinite depths of darkness, where stars have long faded, "
        "**The Void** awaits your arrival.\n\n"
        "🔱 **Enter The Void now and claim your eternal crown.**\n\n"
        "**The Void bows to no one... except you.**"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔱 ENTER THE VOID 🔱", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=markup)

# --- مسیرهای API ---
@app.get("/", response_class=HTMLResponse)
async def home():
    return FileResponse("index.html")

@app.get("/api/gallery/{user_id}")
async def fetch_gallery(user_id: int):
    results = []
    prefix = f"user_{user_id}_"
    if os.path.exists(OUTPUT_DIR):
        for f in os.listdir(OUTPUT_DIR):
            if f.startswith(prefix):
                results.append({"url": f"/static/outputs/{f}", "dna": f.split('_')[-1].split('.')[0]})
    return {"images": results[::-1]}

@app.post("/api/mint")
async def process_mint(request: Request):
    payload = await request.json()
    uid = payload.get('u')
    text = payload.get('b', 'THE UNNAMED')
    code = random.randint(1000000, 9999999)
    
    path, fname = forge_artifact(text, code, uid)
    
    if path and bot:
        async def notify():
            try:
                await bot.send_photo(chat_id=uid, photo=FSInputFile(path), 
                                     caption=f"🔱 **ASCENSION SEALED**\nDNA: `{code}`")
            except Exception as e:
                logger.error(f"Telegram send error: {e}")
        asyncio.create_task(notify())
        
    return {"status": "success", "url": f"/static/outputs/{fname}"}

# --- بخش حیاتی: استارت‌آپ بدون توقف ---
@app.on_event("startup")
async def startup_event():
    global bot
    # پاکسازی نهایی توکن
    clean_token = "".join(API_TOKEN.split())
    
    try:
        # ساخت شیء Bot به صورت Local در زمان اجرا برای عبور از فیلتر اولیه
        bot = Bot(token=clean_token)
        await bot.delete_webhook(drop_pending_updates=True)
        # اجرای Polling بدون متوقف کردن FastAPI
        asyncio.create_task(dp.start_polling(bot))
        logger.info("✅ THE VOID IS ONLINE")
    except Exception as e:
        # اگر توکن باز هم اشتباه بود، برنامه کرش نمی‌کند و سایت بالا می‌ماند
        logger.error(f"❌ BOT ERROR: {e}")
        logger.info("Site is still running but bot is disabled.")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
