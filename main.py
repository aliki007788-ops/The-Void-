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

# --- پیکربندی لاگ ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- تنظیمات توکن و آدرس ---
# توکن را اینجا بگذارید. کد پایین هرگونه کاراکتر مخفی را پاک می‌کند.
RAW_TOKEN = "YOUR_BOT_TOKEN_HERE" 
API_TOKEN = "".join(RAW_TOKEN.split()) # حذف تمام فضاهای خالی و خطوط جدید

WEBAPP_URL = "https://the-void-1.onrender.com"

# --- مقداردهی اولیه ---
app = FastAPI()

# استفاده از Session برای جلوگیری از خطاهای اعتبارسنجی توکن در برخی محیط‌ها
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# مدیریت مسیرهای فایل
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
OUTPUT_DIR = os.path.join(STATIC_DIR, "outputs")

os.makedirs(OUTPUT_DIR, exist_ok=True)

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# --- تولید آرتیفکت امپراطوری (Pillow) ---
def forge_artifact(text, dna, user_id):
    img = Image.new('RGB', (800, 800), color=(1, 1, 1))
    draw = ImageDraw.Draw(img)
    gold_tone = (212, 175, 55)
    
    # طراحی حاشیه سلطنتی
    draw.rectangle([20, 20, 780, 780], outline=gold_tone, width=4)
    draw.rectangle([40, 40, 760, 760], outline=gold_tone, width=1)
    
    content = f"THE VOID\n\nSOVEREIGN: {user_id}\nBURDEN: {text.upper()}\nDNA: {dna}"
    draw.text((400, 400), content, fill=gold_tone, anchor="mm", align="center")
    
    filename = f"user_{user_id}_{dna}.jpg"
    filepath = os.path.join(OUTPUT_DIR, filename)
    img.save(filepath, "JPEG", quality=90)
    return filepath, filename

# --- بخش ربات (پیام حماسی و دکمه ورود) ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_name = message.from_user.first_name
    welcome_msg = (
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
    await message.answer(welcome_msg, parse_mode="Markdown", reply_markup=markup)

# --- API Endpoints ---
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
    text = payload.get('b', 'THE UNKNOWN')
    code = random.randint(1000000, 9999999)
    
    path, fname = forge_artifact(text, code, uid)
    
    # ارسال ناهمگام به تلگرام
    async def notify():
        try:
            await bot.send_photo(
                chat_id=uid, 
                photo=FSInputFile(path), 
                caption=f"🔱 **ASCENSION SEALED**\nDNA: `{code}`\nBurden: {text}"
            )
        except Exception as e:
            logger.error(f"TG Error: {e}")

    asyncio.create_task(notify())
    return {"status": "success", "url": f"/static/outputs/{fname}"}

# --- چرخه حیات و مدیریت پورت Render ---
@app.on_event("startup")
async def start_event():
    # حذف وب‌هوک برای جلوگیری از تداخل
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(dp.start_polling(bot))
    logger.info("THE VOID IS NOW ONLINE")

if __name__ == "__main__":
    import uvicorn
    # Render به صورت خودکار پورت را مدیریت می‌کند
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
