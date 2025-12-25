import os
import random
import asyncio
import logging
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile

# --- تنظیمات لاگ ---
logging.basicConfig(level=logging.INFO)

# --- متغیرهای اصلی ---
TOKEN = "YOUR_BOT_TOKEN_HERE"
WEBAPP_URL = "https://the-void-1.onrender.com"

# --- مقداردهی اولیه FastAPI و Aiogram ---
app = FastAPI()
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ایجاد پوشه ذخیره تصاویر
OUTPUT_DIR = "static/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# سرو کردن فایل‌های استاتیک و HTML
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- بخش ربات تلگرام (Aiogram 3) ---

@dp.message(CommandStart())
async def start_command(message: types.Message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"🔱 **درود بر تو، {user_name.upper()}** 🔱\n\n"
        "به تالار **THE VOID** خوش آمدی. جایی که رنج‌های تو به آثار جاودانه‌ی طلایی تبدیل می‌شوند.\n\n"
        "🏛️ *سرنوشت در انتظار توست...*"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔱 ENTER THE VOID 🔱", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=kb)

# --- بخش API هماهنگ با پنل HTML شما ---

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    return FileResponse("index.html")

@app.get("/api/gallery/{user_id}")
async def get_gallery(user_id: int):
    user_images = []
    prefix = f"user_{user_id}_"
    
    if os.path.exists(OUTPUT_DIR):
        for filename in os.listdir(OUTPUT_DIR):
            if filename.startswith(prefix):
                user_images.append({
                    "url": f"/static/outputs/{filename}",
                    "dna": filename.split('_')[-1].split('.')[0]
                })
    
    user_images.sort(key=lambda x: x['dna'], reverse=True)
    return {"images": user_images}

@app.post("/api/mint")
async def mint_artifact(request: Request):
    data = await request.json()
    user_id = data.get('u')
    burden = data.get('b', 'Unknown Burden')
    plan_type = data.get('p', 'eternal')
    
    artifact_id = random.randint(1000000, 9999999)
    filename = f"user_{user_id}_art_{artifact_id}.jpg"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    # تولید دیتای تستی برای تصویر
    with open(filepath, "wb") as f:
        f.write(os.urandom(2048))
    
    # ارسال عکس به تلگرام در پس‌زمینه (برای سرعت بیشتر API)
    async def send_to_telegram():
        try:
            photo = FSInputFile(filepath)
            caption = (f"🔱 **ASCENSION COMPLETE** 🔱\n\n"
                       f"📜 **Burden:** *{burden}*\n"
                       f"🧬 **DNA:** `{artifact_id}`")
            await bot.send_photo(chat_id=user_id, photo=photo, caption=caption, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Telegram send error: {e}")

    asyncio.create_task(send_to_telegram())
    
    return {"status": "success", "dna": artifact_id, "url": f"/static/outputs/{filename}"}

# --- مدیریت چرخه حیات (Lifecycle) برای اجرای همزمان Polling و FastAPI ---

@app.on_event("startup")
async def on_startup():
    # حذف وب‌هوک قدیمی برای جلوگیری از خطای 404 در لاگ‌های رندر
    await bot.delete_webhook(drop_pending_updates=True)
    # اجرای Polling در پس‌زمینه
    asyncio.create_task(dp.start_polling(bot))
    logging.info("Bot Polling started...")

@app.on_event("shutdown")
async def on_shutdown():
    await bot.session.close()

if __name__ == "__main__":
    import uvicorn
    # Render پورت را از متغیر PORT می‌گیرد
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
