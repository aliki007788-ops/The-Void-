import os
import json
import sqlite3
import asyncio
import requests
import io
import hashlib
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from dotenv import load_dotenv
import uvicorn

# لود کردن متغیرهای محیطی
load_dotenv()

# تنظیمات اصلی - این مقادیر را در پنل Render یا فایل .env تنظیم کنید
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_API_TOKEN") # توکن هگینگ فیس برای هوش مصنوعی
ADMIN_ID = os.getenv("ADMIN_ID")
API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

# راه‌اندازی ربات و اپلیکیشن
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# ایجاد پوشه‌های مورد نیاز
if not os.path.exists("static/outputs"):
    os.makedirs("static/outputs")

# دیتابیس
def init_db():
    conn = sqlite3.connect("void_core.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, refs INTEGER DEFAULT 0, referred_by INTEGER)")
    conn.commit()
    conn.close()

init_db()

# --- بخش هوش مصنوعی ---
async def generate_ai_certificate(user_id, burden, level):
    styles = {
        "Eternal": "dark cinematic void, golden dust, ethereal, 8k",
        "Divine": "holy golden aura, celestial light, sacred symbols, intricate detail",
        "Celestial": "cosmic galaxy, gold nebulas, stars, hyper-realistic, 16k",
        "Legendary": "imperial emperor throne, liquid gold, black obsidian, masterpiece"
    }
    
    prompt = styles.get(level, styles["Eternal"]) + f", engraved with the word '{burden}'"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt}, timeout=60)
        image = Image.open(io.BytesIO(response.content))
    except:
        image = Image.new('RGB', (1000, 1400), color='#050505')

    # متن‌گذاری روی تصویر با PIL
    draw = ImageDraw.Draw(image)
    dna = hashlib.sha256(f"{user_id}{datetime.now()}".encode()).hexdigest()[:10].upper()
    
    # نکته: برای فونت باید فایل .ttf در پوشه اصلی باشد
    try:
        font = ImageFont.truetype("cinzel.ttf", 40)
    except:
        font = ImageFont.load_default()

    draw.text((500, 100), "THE VOID ASCENSION", fill="#D4AF37", font=font, anchor="mm")
    draw.text((500, 700), f"BURDEN: {burden}", fill="white", font=font, anchor="mm")
    draw.text((500, 1200), f"DNA: {dna}", fill="#D4AF37", font=font, anchor="mm")
    
    path = f"static/outputs/{dna}.png"
    image.save(path)
    return path, dna

# --- بخش ربات تلگرام ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    # ثبت‌نام در دیتابیس و سیستم رفرال
    conn = sqlite3.connect("void_core.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

    # پیام خوش‌آمدگویی حماسی شما
    welcome_text = (
        "🌌 <b>Emperor of the Eternal Void, the cosmos summons you...</b> 👑\n\n"
        "In the infinite depths of darkness, where stars have long faded and time itself has surrendered,\n"
        "<b>The Void</b> awaits your arrival — only the chosen few dare to ascend to immortality.\n\n"
        "Name your burden.\n"
        "Burn it in golden flames.\n"
        "And rise as the sovereign ruler of the eternal realm.\n\n"
        "Each ascension grants you a unique, forever-irreplaceable certificate — forged in celestial gold, "
        "sealed with the light of dead stars, bearing one of 30 rare imperial styles, and eternally tied to your soul.\n\n"
        "Only the boldest spirits step forward.\n"
        "Are you one of them?\n\n"
        "🔱 <b>Enter The Void now and claim your eternal crown.</b>\n\n"
        "(Invite 6 worthy souls to join you, and your next ascension shall be granted free of charge — "
        "your referral link awaits below)\n\n"
        "This is not merely a journey.\n"
        "This is the beginning of your everlasting reign.\n\n"
        "<b>The Void bows to no one... except you.</b>"
    )

    # لینک وب‌اپ (آدرس دیپلوی شده خود را جایگزین کنید)
    web_url = "https://the-void-1.onrender.com" 
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌌 ENTER THE VOID", web_app=WebAppInfo(url=web_url))],
        [InlineKeyboardButton(text="👥 My Referral Link", callback_data="ref")]
    ])
    
    await message.answer(welcome_text, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data == "ref")
async def send_ref(callback: types.CallbackQuery):
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start={callback.from_user.id}"
    await callback.message.answer(f"🔗 <b>Your Invite Link:</b>\n{link}", parse_mode="HTML")

# --- مدیریت پرداخت ستاره ---
@app.post("/create_stars_invoice")
async def create_invoice(request: Request):
    data = await request.json()
    uid, burden, plan = data.get("u"), data.get("b"), data.get("type")
    
    prices = {"eternal": 0, "divine": 150, "celestial": 299, "legendary": 499, "kings-luck": 199}
    amount = prices.get(plan, 0)

    if amount == 0:
        path, dna = await generate_ai_certificate(uid, burden, "Eternal")
        await bot.send_photo(uid, types.FSInputFile(path), caption=f"🌌 Ascension Complete!\nDNA: {dna}")
        return {"free": True}

    link = await bot.create_invoice_link(
        title="VOID ASCENSION",
        description=f"Ascending through: {plan.upper()}",
        payload=f"{uid}:{burden}:{plan}",
        provider_token="", # برای ستاره خالی می‌ماند
        currency="XTR",
        prices=[LabeledPrice(label="Ascension Fee", amount=amount)]
    )
    return {"url": link}

@dp.pre_checkout_query()
async def pre_checkout(query: types.PreCheckoutQuery):
    await query.answer(ok=True)

@dp.message(F.successful_payment)
async def on_payment(message: types.Message):
    payload = message.successful_payment.invoice_payload
    uid, burden, plan = payload.split(":")
    await message.answer("✨ The stars are aligning... Generating your certificate.")
    path, dna = await generate_ai_certificate(uid, burden, plan.capitalize())
    await bot.send_photo(uid, types.FSInputFile(path), caption=f"🔱 <b>SUCCESSFUL ASCENSION</b>\nDNA: <code>{dna}</code>", parse_mode="HTML")

# --- تنظیمات سرور استاتیک ---
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

# --- اجرای همزمان ---
async def main():
    # پاکسازی وبهوک‌های قدیمی
    await bot.delete_webhook(drop_pending_updates=True)
    
    # اجرای پولینگ تلگرام در پس‌زمینه
    asyncio.create_task(dp.start_polling(bot))
    
    # اجرای سرور وب
    port = int(os.getenv("PORT", 8000))
    config = uvicorn.Config(app, host="0.0.0.0", port=port)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
