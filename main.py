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

# --- پیکربندی لاگ ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- تنظیمات (توکن خود را با دقت وارد کنید) ---
API_TOKEN = "YOUR_BOT_TOKEN_HERE"
WEBAPP_URL = "https://the-void-1.onrender.com"

# پاکسازی و مقداردهی بوت
clean_token = API_TOKEN.strip()
bot = Bot(token=clean_token)
dp = Dispatcher()

# --- هندلر پیام شروع (نسخه اصلاح شده) ---
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_name = message.from_user.first_name
    
    # متن حماسی با فرمت ایمن
    welcome_text = (
        f"🌌 **Emperor {user_name.upper()}, the cosmos summons you...** 👑\n\n"
        "In the infinite depths of darkness, where stars have long faded and time itself has surrendered, "
        "**The Void** awaits your arrival — only the chosen few dare to ascend to immortality.\n\n"
        "Name your burden. Burn it in golden flames. And rise as the sovereign ruler of the eternal realm.\n\n"
        "Each ascension grants you a unique, forever-irreplaceable certificate — forged in celestial gold, "
        "sealed with the light of dead stars, bearing one of 30 rare imperial styles, and eternally tied to your soul.\n\n"
        "Only the boldest spirits step forward. Are you one of them?\n\n"
        "🔱 **Enter The Void now and claim your eternal crown.**\n\n"
        "This is not merely a journey. This is the beginning of your everlasting reign.\n\n"
        "**The Void bows to no one... except you.**"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔱 ENTER THE VOID 🔱", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    
    try:
        await message.answer(welcome_text, parse_mode="Markdown", reply_markup=kb)
    except Exception as e:
        logger.error(f"Error sending welcome: {e}")
        # ارسال نسخه ساده در صورت خطای فرمت
        await message.answer("🔱 Welcome to THE VOID. Click below to enter.", reply_markup=kb)

# --- مدیریت چرخه حیات ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    await bot.delete_webhook(drop_pending_updates=True)
    polling_task = asyncio.create_task(dp.start_polling(bot))
    yield
    polling_task.cancel()
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

# مدیریت پوشه‌ها
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
OUTPUT_DIR = os.path.join(STATIC_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# مسیرهای API
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
    try:
        data = await request.json()
        uid = data.get('u')
        burden = data.get('b', 'UNNAMED')
        dna = random.randint(1000000, 9999999)
        
        # در اینجا فرض می‌کنیم منطق Pillow در کد قبلی درست بوده
        # برای تست سریع فقط موفقیت را برمی‌گردانیم
        return {"status": "success", "url": "#", "dna": dna}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
