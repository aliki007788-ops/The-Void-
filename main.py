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
from PIL import Image, ImageDraw, ImageFont

# --- تنظیمات لاگ ---
logging.basicConfig(level=logging.INFO)

# --- تنظیمات اصلی (توکن و آدرس خود را جایگزین کنید) ---
API_TOKEN = "YOUR_BOT_TOKEN_HERE" 
WEBAPP_URL = "https://the-void-1.onrender.com"

app = FastAPI()
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

OUTPUT_DIR = "static/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# --- تابع فورج کردن لوح طلایی (Pillow) ---
def forge_golden_tablet(burden_text, dna, user_id):
    # ایجاد یک بوم با کیفیت بالا
    width, height = 1000, 1000
    img = Image.new('RGB', (width, height), color=(2, 2, 2)) # مشکی مطلق
    draw = ImageDraw.Draw(img)
    
    # رسم کادرهای طلایی چندلایه برای حس امپراطوری
    gold_color = (212, 175, 55)
    draw.rectangle([30, 30, 970, 970], outline=gold_color, width=8)
    draw.rectangle([50, 50, 950, 950], outline=gold_color, width=2)
    
    # متن آرتیفکت
    content = f"THE VOID ASCENSION\n\nBURDEN:\n{burden_text.upper()}\n\nDNA: {dna}\nUSER: {user_id}"
    
    # در صورت وجود فونت، آن را بارگذاری کنید. در غیر این صورت از فونت پیش‌فرض استفاده می‌شود.
    draw.text((width/2, height/2), content, fill=gold_color, anchor="mm", align="center")
    
    filename = f"user_{user_id}_art_{dna}.jpg"
    filepath = os.path.join(OUTPUT_DIR, filename)
    img.save(filepath, "JPEG", quality=95)
    return filepath, filename

# --- بخش ربات تلگرام (با متن حماسی شما) ---

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_name = message.from_user.first_name
    referral_link = f"https://t.me/your_bot_username?start={message.from_user.id}"
    
    # متن حماسی ارسالی شما
    welcome_text = (
        f"🌌 **Emperor {user_name.upper()}, the cosmos summons you...** 👑\n\n"
        "In the infinite depths of darkness, where stars have long faded and time itself has surrendered, "
        "**The Void** awaits your arrival — only the chosen few dare to ascend to immortality.\n\n"
        "Name your burden. Burn it in golden flames. And rise as the sovereign ruler of the eternal realm.\n\n"
        "Each ascension grants you a unique, forever-irreplaceable certificate — forged in celestial gold, "
        "bearing one of 30 rare imperial styles, and eternally tied to your soul.\n\n"
        "Only the boldest spirits step forward. Are you one of them?\n\n"
        "🔱 **Enter The Void now and claim your eternal crown.**\n\n"
        f"🔗 **Your Referral Link:** `{referral_link}`\n"
        "(Invite 6 worthy souls, and your next ascension shall be free!)\n\n"
        "**The Void bows to no one... except you.**"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔱 ENTER THE VOID 🔱", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=kb)

# --- API ENDPOINTS ---

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    return FileResponse("index.html")

@app.get("/api/gallery/{user_id}")
async def get_gallery(user_id: int):
    user_images = []
    prefix = f"user_{user_id}_"
    if os.path.exists(OUTPUT_DIR):
        for f in os.listdir(OUTPUT_DIR):
            if f.startswith(prefix):
                user_images.append({"url": f"/static/outputs/{f}", "dna": f.split('_')[-1].split('.')[0]})
    user_images.sort(key=lambda x: x['dna'], reverse=True)
    return {"images": user_images}

@app.post("/api/mint")
async def mint_api(request: Request):
    try:
        data = await request.json()
        u_id = data.get('u')
        burden = data.get('b', 'THE UNNAMED')
        
        dna = random.randint(1111111, 9999999)
        filepath, filename = forge_golden_tablet(burden, dna, u_id)
        
        # ارسال فوری به تلگرام
        async def send_tg():
            try:
                photo = FSInputFile(filepath)
                await bot.send_photo(
                    chat_id=u_id, 
                    photo=photo, 
                    caption=f"🔱 **THE VOID HAS SPOKEN** 🔱\n\nYour burden *{burden}* has been consumed.\nDNA: `{dna}`\n\nRise, Sovereign.",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logging.error(f"TG Error: {e}")

        asyncio.create_task(send_tg())
        return {"status": "success", "dna": dna, "url": f"/static/outputs/{filename}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- STARTUP ---

@app.on_event("startup")
async def on_startup():
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(dp.start_polling(bot))
    logging.info("THE VOID IS ACTIVE")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
