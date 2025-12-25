import os
import json
import random
import sqlite3
import asyncio
import uvicorn
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
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()

# --- تنظیمات اصلی ---
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_API_TOKEN") # توکن هوش مصنوعی هگینگ فیس
API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
app = FastAPI()

# --- دیتابیس ---
def init_db():
    conn = sqlite3.connect("void_core.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, refs INTEGER DEFAULT 0, referred_by INTEGER)")
    conn.commit()
    conn.close()

init_db()

# --- بخش هوش مصنوعی (AI Core) ---
def generate_dna(user_id, level):
    seed = f"{user_id}{level}{datetime.now()}".encode()
    return hashlib.sha256(seed).hexdigest()[:10].upper()

async def create_certificate(user_id, burden, level):
    """تولید تصویر گواهی با هوش مصنوعی و متن گذاری"""
    # ۱۵۰ سبک حرفه ای (خلاصه شده برای پایداری در این فایل)
    styles = {
        "Eternal": "luxurious dark obsidian texture, gold filigree, mystical lighting, 8k",
        "Divine": "imperial Byzantine mosaic, heavy gold leaf, sacred divine aura, masterpiece",
        "Celestial": "celestial phoenix nebula, cosmic gold dust, sacred geometry, 16k",
        "Legendary": "supreme void emperor throne, liquid stars and gold, hyper-realistic"
    }
    
    prompt = f"{styles.get(level, styles['Eternal'])}, focal point inscribed with '{burden}'"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt}, timeout=60)
        image = Image.open(io.BytesIO(response.content))
    except:
        image = Image.new('RGB', (1000, 1414), color='#050505')

    canvas = image.resize((1000, 1414))
    draw = ImageDraw.Draw(canvas)
    dna = generate_dna(user_id, level)

    try:
        font_main = ImageFont.truetype("cinzel.ttf", 55)
        font_sub = ImageFont.truetype("cinzel.ttf", 35)
    except:
        font_main = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    draw.text((500, 150), "VOID ASCENSION", fill="#D4AF37", font=font_main, anchor="mm")
    draw.text((500, 707), f"'{burden}'", fill="white", font=font_sub, anchor="mm")
    draw.text((500, 1250), f"DNA: {dna}", fill="#D4AF37", font=font_sub, anchor="mm")
    
    path = f"static/outputs/{dna}.png"
    if not os.path.exists("static/outputs"): os.makedirs("static/outputs")
    canvas.save(path)
    return path, dna

# --- هندلر استارت با پیام خوش‌آمدگویی جدید ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    inviter_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    
    conn = sqlite3.connect("void_core.db")
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not c.fetchone():
        c.execute("INSERT INTO users (id, referred_by) VALUES (?, ?)", (user_id, inviter_id))
        if inviter_id:
            c.execute("UPDATE users SET refs = refs + 1 WHERE id = ?", (inviter_id,))
        conn.commit()
    conn.close()

    web_app_url = "https://the-void-1.onrender.com"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌌 ENTER THE VOID", web_app=WebAppInfo(url=web_app_url))],
        [InlineKeyboardButton(text="👥 Referral Link", callback_data="ref_link")]
    ])

    # متن دقیق درخواستی شما
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

    await message.answer(welcome_text, reply_markup=kb, parse_mode="HTML")

# --- منطق پرداخت و صدور گواهی ---
@app.post("/create_stars_invoice")
async def create_invoice(request: Request):
    data = await request.json()
    uid, burden, plan = data.get("u"), data.get("b"), data.get("type")
    
    prices = {"eternal": 0, "divine": 150, "celestial": 299, "legendary": 499, "kings-luck": 199}
    amount = prices.get(plan, 0)

    if amount == 0:
        path, dna = await create_certificate(uid, burden, "Eternal")
        await bot.send_photo(uid, types.FSInputFile(path), caption=f"🌌 Ascension Complete!\nDNA: {dna}")
        return {"free": True}

    link = await bot.create_invoice_link(
        title="VOID ASCENSION",
        description=f"Level: {plan.upper()}",
        payload=f"{uid}:{burden}:{plan}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Ascension Fee", amount=amount)]
    )
    return {"url": link}

@dp.pre_checkout_query()
async def pre_checkout(query: types.PreCheckoutQuery):
    await query.answer(ok=True)

@dp.message(F.successful_payment)
async def on_payment(message: types.Message):
    uid, burden, plan = message.successful_payment.invoice_payload.split(":")
    await message.answer("✨ Forging your eternal certificate in the cosmic fire...")
    path, dna = await create_certificate(uid, burden, plan.capitalize())
    await bot.send_photo(uid, types.FSInputFile(path), caption=f"🌌 <b>ASCENSION SUCCESSFUL</b>\nDNA: <code>{dna}</code>", parse_mode="HTML")

# --- سرور و اجرا ---
@dp.callback_query(F.data == "ref_link")
async def send_ref_link(callback: types.CallbackQuery):
    bot_user = await bot.get_me()
    link = f"https://t.me/{bot_user.username}?start={callback.from_user.id}"
    await callback.message.answer(f"🔗 <b>Your Referral Link:</b>\n<code>{link}</code>", parse_mode="HTML")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open("static/index.html", "r", encoding="utf-8") as f: return f.read()

async def main():
    asyncio.create_task(dp.start_polling(bot))
    config = uvicorn.Config(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
    await uvicorn.Server(config).serve()

if __name__ == "__main__":
    asyncio.run(main())
