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

# --- تنظیمات لاگینگ برای مشاهده دقیق وضعیت در Render ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- تنظیمات اصلی (توکن خود را با دقت جایگذاری کنید) ---
API_TOKEN = "YOUR_BOT_TOKEN_HERE"
WEBAPP_URL = "https://the-void-1.onrender.com"

# --- مقداردهی اولیه ---
# پاکسازی توکن از هرگونه کاراکتر مخفی
clean_token = "".join(API_TOKEN.split())
bot = Bot(token=clean_token)
dp = Dispatcher()

# --- بخش ربات: پیام خوش‌آمدگویی حماسی شما ---
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_name = message.from_user.first_name
    
    # متن حماسی که ارسال کردید
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
    
    # دکمه ورود به اپلیکیشن (WebApp)
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔱 ENTER THE VOID 🔱", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=markup)
    logger.info(f"Welcome message sent to {user_id}")

# --- مدیریت چرخه حیات (Lifespan) برای اجرای همزمان ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # این بخش هنگام استارت شدن سرور اجرا می‌شود
    logger.info("🚀 Starting THE VOID system...")
    await bot.delete_webhook(drop_pending_updates=True)
    
    # اجرای Polling در پس‌زمینه
    polling_task = asyncio.create_task(dp.start_polling(bot))
    logger.info("✅ Bot is polling and WebApp is ready.")
    
    yield
    
    # این بخش هنگام خاموش شدن سرور اجرا می‌شود
    polling_task.cancel()
    await bot.session.close()

# --- تنظیمات FastAPI ---
app = FastAPI(lifespan=lifespan)

# مدیریت فایل‌های استاتیک و خروجی
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
OUTPUT_DIR = os.path.join(STATIC_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# --- تابع تولید آرتیفکت امپراطوری ---
def forge_artifact(text, dna, user_id):
    img = Image.new('RGB', (800, 800), color=(2, 2, 2))
    draw = ImageDraw.Draw(img)
    gold = (212, 175, 55)
    
    # رسم کادر طلایی
    draw.rectangle([30, 30, 770, 770], outline=gold, width=6)
    
    content = f"THE VOID ASCENSION\n\nSOVEREIGN: {user_id}\nBURDEN: {text.upper()}\nDNA: {dna}"
    draw.text((400, 400), content, fill=gold, anchor="mm", align="center")
    
    filename = f"user_{user_id}_{dna}.jpg"
    filepath = os.path.join(OUTPUT_DIR, filename)
    img.save(filepath, "JPEG")
    return filepath, filename

# --- مسیرهای API هماهنگ با فرانت‌اِند ---
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
    data = await request.json()
    uid = data.get('u')
    burden = data.get('b', 'UNNAMED BURDEN')
    dna_code = random.randint(1000000, 9999999)
    
    path, fname = forge_artifact(burden, dna_code, uid)
    
    # ارسال آرتیفکت به تلگرام به صورت ناهمگام
    async def send_artifact():
        try:
            await bot.send_photo(
                chat_id=uid,
                photo=FSInputFile(path),
                caption=f"🔱 **ARTEFACT FORGED**\n\nYour burden has been consumed by the golden flames.\nDNA: `{dna_code}`"
            )
        except Exception as e:
            logger.error(f"Failed to send photo: {e}")

    asyncio.create_task(send_artifact())
    
    return {"status": "success", "url": f"/static/outputs/{fname}", "dna": dna_code}

if __name__ == "__main__":
    import uvicorn
    # هماهنگی با پورت رندر
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
