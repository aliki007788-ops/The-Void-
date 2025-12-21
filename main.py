import os
import json
import base64
import tempfile
import secrets
import random
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup,
    Update, FSInputFile, LabeledPrice
)
from cert_gen import create_certificate
from dotenv import load_dotenv

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(storage=MemoryStorage())
app = FastAPI()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
PRICE_PREMIUM = 120

VIP_FILE = "vip_codes.txt"

def load_vip_codes():
    if os.path.exists(VIP_FILE):
        with open(VIP_FILE, "r", encoding="utf-8") as f:
            return set(line.strip().upper() for line in f if line.strip())
    return set()

def save_vip_codes(codes):
    with open(VIP_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(codes)))

VIP_CODES = load_vip_codes()

async def send_nft(uid: int, burden: str, photo_path: str = None, is_gift: bool = False):
    nft_path, style_name = create_certificate(uid, burden, photo_path)
    
    if is_gift:
        caption = (
            "🔱 <b>DIVINE PARTNERSHIP GRANTED</b>\n\n"
            f"\"<i>{burden.upper()}</i>\"\n\n"
            f"<b>{style_name}</b>\n\n"
            "Your noble essence has been eternally enshrined\n"
            "in the sacred archive of the Void.\n\n"
            "A masterpiece forged for eternity."
        )
    else:
        caption = (
            "🔱 <b>ASCENSION COMPLETE</b>\n\n"
            f"\"<i>{burden.upper()}</i>\"\n\n"
            "HAS BEEN CONSUMED BY THE ETERNAL VOID\n\n"
            f"<b>{style_name}</b>\n\n"
            "Your soul has received its eternal crown of glory.\n"
            "A unique masterpiece, forever preserved.\n"
            f"Holder ID: <code>{uid}</code>\n"
            "Timestamp: <code>2025.VO-ID</code>"
        )
    
    await bot.send_document(uid, FSInputFile(nft_path), caption=caption, parse_mode="HTML")
    
    for p in [nft_path, photo_path]:
        if p and os.path.exists(p):
            try:
                os.remove(p)
            except:
                pass

# /start – متن کامل خوش‌آمدگویی انگلیسی
@dp.message(F.text == "/start")
async def start(message: types.Message):
    welcome_text = """
🌌 <b>WELCOME, WANDERER OF THE COSMOS</b> 🌌

The Eternal Void has sensed your presence.

In the year <b>2025.VO-ID</b>, the ancient gates have parted once more — revealing a realm where burdens are transformed into eternal glory.

<b>VOID ASCENSION CERTIFICATE</b>

Two sacred paths await your offering:

<b>1. Free Eternal Ascension</b>
• Simply send your <i>Burden Title</i> directly in this chat
• Receive a magnificent certificate forged in cosmic gold instantly

<b>2. Divine Ascension (120 ⭐)</b>
• Tap "ENTER THE VOID" below
• Crown yourself with your soul image (photo)
• Receive the ultimate royal glow and divine imprint

Each certificate is adorned with one of <b>30 sacred styles</b>.

Once consumed, your burden is eternal.

Your referral link:
<code>https://t.me/livevoidbot?start=ref_{message.from_user.id}</code>

Share it and grow the Void.
    """.strip()

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔱 ENTER THE VOID", web_app=WebAppInfo(url=f"{os.getenv('WEBHOOK_URL')}/static/index.html"))
    ]])

    await message.answer(welcome_text, reply_markup=kb, parse_mode="HTML")

# --- دستورات ویژه ادمین (اولویت بالا) ---
@dp.message(Command("divine"), F.from_user.id == ADMIN_ID)
async def admin_divine_text(message: types.Message):
    args = message.text.split(maxsplit=1)
    burden = args[1].strip()[:50] if len(args) > 1 else "Divine Admin Creation"
    await message.answer("👑 <b>Admin Divine Forging...</b>", parse_mode="HTML")
    await send_nft(message.from_user.id, burden)

@dp.message(F.photo, F.from_user.id == ADMIN_ID)
async def admin_divine_photo(message: types.Message):
    burden = message.caption.strip()[:50] if message.caption else "Divine Gift from the Void"
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    photo_path = f"admin_divine_{message.from_user.id}.jpg"
    await bot.download_file(file.file_path, photo_path)
    await message.answer("👑 <b>Admin Divine Forging...</b>", parse_mode="HTML")
    await send_nft(message.from_user.id, burden, photo_path)

# --- حالت رایگان عادی ---
@dp.message(F.text, ~F.text.startswith("/"))
async def free_ascension(message: types.Message):
    burden = message.text.strip()
    if len(burden) < 3:
        await message.answer("🔥 Your burden is too light. Enter at least 3 characters.\nExample: Emperor of Silence")
        return
    if len(burden) > 50:
        burden = burden[:47] + "..."
    
    await message.answer("🌌 <b>THE VOID ACCEPTS YOUR OFFERING</b>\n\nForging your eternal certificate...\nOne moment, wanderer.", parse_mode="HTML")
    await send_nft(message.from_user.id, burden)
    
    premium_text = """
🎁 <b>YOUR ETERNAL CERTIFICATE HAS BEEN FORGED</b>

This is merely the beginning.

For the ultimate <b>Divine Ascension</b> with your soul image and royal glow:

Tap the sacred portal below 👇
    """.strip()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔱 DIVINE ASCENSION WITH PHOTO", web_app=WebAppInfo(url=f"{os.getenv('WEBHOOK_URL')}/static/index.html"))
    ]])
    
    await message.answer(premium_text, reply_markup=kb, parse_mode="HTML")

# --- پرداخت Divine از وب‌اپ ---
async def create_invoice_logic(data):
    uid = data['u']
    burden_raw = data.get('b', '').strip()
    burden_upper = burden_raw.upper()
    if burden_raw in VIP_CODES or burden_upper in VIP_CODES:
        VIP_CODES.discard(burden_raw)
        VIP_CODES.discard(burden_upper)
        save_vip_codes(VIP_CODES)
        await send_nft(uid, burden_raw, None, is_gift=True)
        return {"free": True}
    
    temp_path = "none"
    if data.get('p'):
        img_data = base64.b64decode(data['p'].split(',')[1])
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        tmp.write(img_data)
        tmp.close()
        temp_path = tmp.name
    
    link = await bot.create_invoice_link(
        title="DIVINE ASCENSION",
        description="Luxurious Soul Crown",
        payload=f"{uid}:{burden_raw}:{temp_path}",
        currency="XTR",
        prices=[LabeledPrice(label="Crown Fee", amount=PRICE_PREMIUM)]
    )
    return {"url": link}

@app.post("/create_stars_invoice")
async def create_invoice_post(request: Request):
    data = await request.json()
    return await create_invoice_logic(data)

@dp.pre_checkout_query()
async def pre_checkout(q: types.PreCheckoutQuery):
    await q.answer(ok=True)

@dp.message(F.successful_payment)
async def successful_payment(message: types.Message):
    parts = message.successful_payment.invoice_payload.split(":")
    uid = int(parts[0])
    burden = parts[1]
    temp_path = parts[2] if parts[2] != "none" else None
    await send_nft(uid, burden, temp_path)

# --- وب‌هوک و استاتیک ---
app.mount("/static", StaticFiles(directory="static"))

@app.post("/webhook")
async def webhook(request: Request):
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.on_event("startup")
async def startup():
    await bot.set_webhook(f"{os.getenv('WEBHOOK_URL')}/webhook")
