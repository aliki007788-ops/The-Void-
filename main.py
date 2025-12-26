import os
import random
import asyncio
import logging
import sqlite3
import requests
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import io

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- تنظیمات ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")  # برای Stable Diffusion
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing!")
if not HF_API_TOKEN:
    logger.warning("HF_API_TOKEN missing - AI image generation disabled (fallback used)")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

WEBAPP_URL = "https://the-void-1.onrender.com"
HF_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"

# --- دیتابیس ---
def init_db():
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY,
                 username TEXT,
                 refs INTEGER DEFAULT 0,
                 free_mints INTEGER DEFAULT 3,
                 total_ascensions INTEGER DEFAULT 0
              )""")
    c.execute("""CREATE TABLE IF NOT EXISTS ascensions (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 plan TEXT,
                 burden TEXT,
                 dna INTEGER,
                 image_url TEXT,
                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
              )""")
    conn.commit()
    conn.close()

init_db()

# --- پیام خوش‌آمدگویی شاهانه ---
WELCOME_MESSAGE = (
    "<b>🌌 Emperor of the Eternal Void, the cosmos summons you...</b>\n\n"
    "In the infinite depths of darkness, where stars have long faded and time itself has surrendered,\n"
    "<b>The Void</b> awaits your arrival — only the chosen few dare to ascend to immortality.\n\n"
    "Name your burden.\n"
    "Burn it in golden flames.\n"
    "And rise as the sovereign ruler of the eternal realm.\n\n"
    "Each ascension grants you a unique, forever-irreplaceable certificate — forged in celestial gold, "
    "sealed with the light of dead stars, bearing one of 30 rare imperial styles, and eternally tied to your soul.\n\n"
    "Only the boldest spirits step forward.\n"
    "<b>Are you one of them?</b>\n\n"
    "🔱 <b>Enter The Void now and claim your eternal crown.</b>\n\n"
    "This is not merely a journey.\n"
    "<b>This is the beginning of your everlasting reign.</b>\n\n"
    "<i>The Void bows to no one... except you.</i>"
)

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or "Unknown"

    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not c.fetchone():
        c.execute("INSERT INTO users (id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()
    conn.close()

    bot_username = (await bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌌 ENTER THE VOID", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="👥 Share Referral Link", url=ref_link)]
    ])

    full_msg = WELCOME_MESSAGE + f"\n\n🔗 <b>Your Referral Link:</b>\n<code>{ref_link}</code>\n\nInvite 6 worthy souls and your next ascension will be free."

    await message.answer(full_msg, parse_mode=ParseMode.HTML, reply_markup=kb)

# --- تولید تصویر با Hugging Face Stable Diffusion img2img ---
async def generate_ai_image(prompt: str, init_image_base64: str):
    if not HF_API_TOKEN:
        return None
    API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "strength": 0.4,
            "guidance_scale": 8.5,
            "num_inference_steps": 50
        },
        "init_image": init_image_base64
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            return response.content
        logger.error(f"HF API Error: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"HF Request failed: {e}")
    return None

# --- FastAPI با Webhook ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # اول وب‌هوک قبلی رو پاک کن
    await bot.delete_webhook(drop_pending_updates=True)
    # بعد وب‌هوک جدید رو ست کن
    webhook_url = "https://the-void-1.onrender.com/webhook"
    await bot.set_webhook(url=webhook_url)
    logger.info(f"Webhook successfully set to {webhook_url}")
    yield
    # در پایان، وب‌هوک رو پاک کن
    await bot.delete_webhook()
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
OUTPUT_DIR = os.path.join(STATIC_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(path):
        return FileResponse(path)
    return "<h1>🌌 THE VOID</h1><p>index.html missing in /static</p>"

# --- Webhook endpoint ---
@app.post("/webhook")
async def webhook(request: Request):
    update = types.Update(**await request.json())
    await dp.feed_update(bot=bot, update=update)
    return {"ok": True}

# --- API مینت ---
@app.post("/api/mint")
async def api_mint(request: Request):
    try:
        data = await request.json()
        user_id = data.get('u')
        plan = data.get('plan', 'eternal')
        burden = data.get('b', 'Unknown Burden')
        photo_base64 = data.get('p')

        if not user_id:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        conn = sqlite3.connect("void_data.db")
        c = conn.cursor()
        c.execute("SELECT free_mints FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()

        if plan == 'eternal' and (not row or row[0] <= 0):
            conn.close()
            return JSONResponse({"error": "No free mints left"}, status_code=403)

        # انتخاب پرامپت (۱۵۰ تا رو اینجا کامل بذار)
        # برای مثال:
        prompt = "luxurious dark royal portrait certificate with ornate golden arabesque frame, intricate diamonds and jewels, cosmic nebula background, sacred geometry mandala, elegant ancient gold font, ultra-detailed masterpiece cinematic lighting"

        image_bytes = None
        if photo_base64 and HF_API_TOKEN:
            image_bytes = await generate_ai_image(prompt, photo_base64)

        if not image_bytes:
            # fallback لوکس با Pillow
            img = Image.new('RGB', (1000, 1400), (5, 5, 5))
            draw = ImageDraw.Draw(img)
            draw.rectangle([50, 50, 950, 1350], outline=(212, 175, 55), width=15)
            draw.rectangle([70, 70, 930, 1330], outline=(169, 135, 0), width=5)
            try:
                font = ImageFont.truetype("arial.ttf", 80)
                font_small = ImageFont.truetype("arial.ttf", 60)
            except:
                font = ImageFont.load_default()
                font_small = ImageFont.load_default()
            draw.text((500, 200), "THE VOID", fill=(255, 215, 0), font=font, anchor="mm")
            draw.text((500, 400), f"{plan.upper()} ASCENSION", fill=(212, 175, 55), font=font, anchor="mm")
            draw.text((500, 700), f"Burden: {burden}", fill=(240, 240, 240), font=font_small, anchor="mm")
            dna = random.randint(1000000, 9999999)
            draw.text((500, 900), f"DNA: {dna}", fill=(169, 135, 0), font=font_small, anchor="mm")
            draw.text((500, 1100), "Forever consumed by The Void", fill=(100, 100, 100), font=font_small, anchor="mm")
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG")
            image_bytes = buffer.getvalue()

        filename = f"{plan}_{user_id}_{random.randint(1000000,9999999)}.jpg"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(image_bytes)

        image_url = f"/static/outputs/{filename}"

        # ذخیره در دیتابیس
        dna = random.randint(1000000, 9999999)
        c.execute("INSERT INTO ascensions (user_id, plan, burden, dna, image_url) VALUES (?, ?, ?, ?, ?)",
                  (user_id, plan, burden, dna, image_url))
        if plan == 'eternal':
            c.execute("UPDATE users SET free_mints = free_mints - 1, total_ascensions = total_ascensions + 1 WHERE id = ?", (user_id,))
        else:
            c.execute("UPDATE users SET total_ascensions = total_ascensions + 1 WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()

        # ارسال تصویر به تلگرام
        try:
            await bot.send_photo(
                chat_id=user_id,
                photo=image_bytes,
                caption=f"🌌 <b>Your {plan.upper()} Ascension is complete!</b>\n\n"
                        f"Burden: {burden}\n"
                        f"DNA: <code>{dna}</code>\n\n"
                        f"The Void has claimed you forever.",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to send photo: {e}")

        return JSONResponse({
            "status": "success",
            "message": "Ascension complete!",
            "image_url": image_url,
            "dna": dna
        })

    except Exception as e:
        logger.error(f"Mint error: {e}")
        return JSONResponse({"error": "The Void is restless."}, status_code=500)

# --- API گالری ---
@app.get("/api/gallery/{user_id}")
async def get_gallery(user_id: int):
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    c.execute("SELECT image_url, plan, dna, burden FROM ascensions WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
    items = [{"image": row[0], "plan": row[1], "dna": row[2], "burden": row[3]} for row in c.fetchall()]
    conn.close()
    return JSONResponse(items)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
