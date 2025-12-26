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

# ۴. پیدا کردن مسیر دقیق فایل‌ها (بسیار مهم برای Render)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# این خط مسیر دقیق فایل index.html را می‌سازد
INDEX_PATH = os.path.join(BASE_DIR, "index.html")
STATIC_DIR = os.path.join(BASE_DIR, "static")
OUTPUT_DIR = os.path.join(STATIC_DIR, "outputs")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- پیام خوش‌آمدگویی حماسی کامل ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"🌌 **Emperor {user_name.upper()}, the cosmos summons you...** 👑\n\n"
        "In the infinite depths of darkness, where stars have long faded and time itself has surrendered, "
        "**The Void** awaits your arrival — only the chosen few dare to ascend to immortality.\n\n"
        "Name your burden. Burn it in golden flames. And rise as the sovereign ruler of the eternal realm.\n\n"
        "🔱 **Enter The Void now and claim your eternal crown.**\n\n"
        "**The Void bows to no one... except you.**"
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
        logger.info(f"✅ THE VOID IS ONLINE. Index Path: {INDEX_PATH}")
    except Exception as e:
        logger.error(f"❌ Bot Startup Error: {e}")
    yield
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

# ۵. سرو کردن فایل‌های استاتیک
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# مسیر اصلی مینی‌اپ با چک کردن وجود فایل
@app.get("/", response_class=HTMLResponse)
async def home():
    if os.path.exists(INDEX_PATH):
        return FileResponse(INDEX_PATH)
    else:
        # اگر باز هم پیدا نشد، لیست فایل‌های موجود در پوشه را در لاگ چاپ می‌کند تا بفهمیم مشکل کجاست
        files_in_dir = os.listdir(BASE_DIR)
        logger.error(f"❌ index.html not found! Files present: {files_in_dir}")
        return HTMLResponse(content=f"Error: index.html not found at {INDEX_PATH}", status_code=404)

# --- API های مورد نیاز مینی‌اپ ---

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
    data = await request.json()
    uid = data.get('u')
    burden = data.get('b', 'THE UNNAMED')
    dna = random.randint(1000000, 9999999)
    
    # تولید تصویر لوح طلایی
    img = Image.new('RGB', (800, 800), color=(5, 5, 5))
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 780, 780], outline=(212, 175, 55), width=5)
    draw.text((400, 400), f"ARTIFACT: {burden}\nDNA: {dna}", fill=(212, 175, 55), anchor="mm", align="center")
    
    fname = f"user_{uid}_{dna}.jpg"
    fpath = os.path.join(OUTPUT_DIR, fname)
    img.save(fpath, "JPEG")
    
    async def send_tg():
        try:
            await bot.send_photo(chat_id=uid, photo=FSInputFile(fpath), 
                                 caption=f"🔱 **ASCENSION SEALED**\nDNA: `{dna}`")
        except Exception as e: logger.error(f"TG Send Error: {e}")

    asyncio.create_task(send_tg())
    return {"status": "success", "url": f"/static/outputs/{fname}"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
