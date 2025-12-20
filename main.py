import os
import json
import base64
import tempfile
import secrets
import random
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, Update, FSInputFile, LabeledPrice
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

async def send_certificate(uid, burden, photo_path=None):
    path, style = create_certificate(uid, burden, photo_path)
    caption = (
        "🔱 <b>DIVINE ASCENSION COMPLETE</b>\n\n"
        f"\"<i>{burden.upper()}</i>\"\n\n"
        f"<b>Style:</b> {style}\n"
        "Your soul has been eternally crowned in glory.\n"
        f"Holder ID: <code>{uid}</code>"
    )
    await bot.send_document(uid, FSInputFile(path), caption=caption, parse_mode="HTML")
    os.remove(path)
    if photo_path and os.path.exists(photo_path):
        os.remove(photo_path)

@dp.message(F.text == "/start")
async def start(message: types.Message):
    text = """
🌌 <b>WELCOME, WANDERER OF THE COSMOS</b>

Two paths to eternity:

<b>Free Ascension:</b> Send any text.
<b>Divine Ascension (120 ⭐):</b> Use the web app to add your soul image.

The Void awaits your offering.
    """
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔱 ENTER THE VOID", web_app=WebAppInfo(url=f"{os.getenv('WEBHOOK_URL')}/static/index.html"))
    ]])
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

# --- ویژگی ویژه ادمین: Divine رایگان با عکس یا متن ---
@dp.message(F.from_user.id == ADMIN_ID, F.photo)
async def admin_divine_photo(message: types.Message):
    burden = message.caption.strip()[:50] if message.caption else "Divine Gift from the Void"
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    photo_path = f"admin_divine_{message.from_user.id}.jpg"
    await bot.download_file(file.file_path, photo_path)
    await message.answer("👑 <b>Admin Divine Forging...</b>\nYour luxurious certificate is being crafted.", parse_mode="HTML")
    await send_certificate(message.from_user.id, burden, photo_path)

@dp.message(F.from_user.id == ADMIN_ID, F.text.startswith("/divine "))
async def admin_divine_text(message: types.Message):
    burden = message.text[8:].strip()[:50]
    if not burden:
        await message.answer("متن burden رو بعد از /divine بنویس.\nمثال: /divine Eternal Sovereign")
        return
    await message.answer("👑 <b>Admin Divine Forging...</b>", parse_mode="HTML")
    await send_certificate(message.from_user.id, burden)

# --- حالت رایگان عادی (فقط متن) ---
@dp.message(F.text & ~F.photo & ~F.text.startswith("/"))
async def free_ascension(message: types.Message):
    burden = message.text.strip()[:50]
    await message.answer("🌌 <b>Forging your eternal certificate...</b>", parse_mode="HTML")
    await send_certificate(message.from_user.id, burden)

# --- پرداخت Divine از وب‌اپ ---
async def create_invoice_logic(data):
    uid = data['u']
    burden = data.get('b', '').strip()
    
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
        payload=f"{uid}:{burden}:{temp_path}",
        currency="XTR",
        prices=[LabeledPrice("Crown Fee", PRICE_PREMIUM)]
    )
    return {"url": link}

@app.post("/create_stars_invoice")
async def invoice(request: Request):
    return await create_invoice_logic(await request.json())

@dp.pre_checkout_query()
async def pre(q: types.PreCheckoutQuery):
    await q.answer(ok=True)

@dp.message(F.successful_payment)
async def paid(message: types.Message):
    parts = message.successful_payment.invoice_payload.split(":")
    await send_certificate(int(parts[0]), parts[1], parts[2] if parts[2] != "none" else None)

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
