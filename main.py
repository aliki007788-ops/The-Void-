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

# ۲. تنظیمات توکن (حتماً توکن خود را در Render یا اینجا قرار دهید)
API_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
WEBAPP_URL = "https://the-void-1.onrender.com"

# ۳. مقداردهی اولیه بوت
bot = Bot(token="".join(API_TOKEN.split()))
dp = Dispatcher()

# ۴. تنظیم دقیق مسیرها برای محیط لینوکس
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# اطمینان از وجود فایل index.html در پوشه اصلی
INDEX_PATH = os.path.join(BASE_DIR, "index.html")
STATIC_DIR = os.path.join(BASE_DIR, "static")
OUTPUT_DIR = os.path.join(STATIC_DIR, "outputs")

# ایجاد پوشه خروجی
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- پیام خوش‌آمدگویی حماسی ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    welcome_text = (
        "🌌 **Emperor, the cosmos summons you...** 👑\n\n"
        "The Void awaits your arrival — only the chosen few dare to ascend to immortality.\n\n"
        "🔱 **Enter The Void now and claim your eternal crown.**"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔱 ENTER THE VOID 🔱", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=markup)

# --- مدیریت چرخه حیات سرور ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        asyncio.create_task(dp.start_polling(bot))
        logger.info("✅ Bot Started Successfully")
    except Exception as e:
        logger.error(f"❌ Bot Error: {e}")
    yield
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

# ۵. اصلاح نحوه سرو کردن فایل‌های استاتیک
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# مسیر اصلی مینی‌اپ (حل مشکل Internal Server Error)
@app.get("/", response_class=HTMLResponse)
async def home():
    if os.path.exists(INDEX_PATH):
        return FileResponse(INDEX_PATH)
    else:
        logger.error("❌ index.html not found in BASE_DIR!")
        return HTMLResponse(content="<h1>Error: index.html not found</h1>", status_code=404)

# --- API Gallery ---
@app.get("/api/gallery/{user_id}")
async def fetch_gallery(user_id: int):
    results = []
    prefix = f"user_{user_id}_"
    if os.path.exists(OUTPUT_DIR):
        for f in os.listdir(OUTPUT_DIR):
            if f.startswith(prefix):
                results.append({"url": f"/static/outputs/{f}", "dna": f.split('_')[-1].split('.')[0]})
    return {"images": results[::-1]}

# --- API Mint ---
@app.post("/api/mint")
async def process_mint(request: Request):
    data = await request.json()
    uid = data.get('u')
    burden = data.get('b', 'UNNAMED')
    dna = random.randint(1000000, 9999999)
    
    # منطق تولید تصویر ساده
    img = Image.new('RGB', (800, 800), color=(2, 2, 2))
    draw = ImageDraw.Draw(img)
    draw.rectangle([30, 30, 770, 770], outline=(212, 175, 55), width=6)
    draw.text((400, 400), f"VOID ARTIFACT\nDNA: {dna}", fill=(212, 175, 55), anchor="mm")
    
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
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
