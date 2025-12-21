import os
import json
import base64
import tempfile
import secrets
import random
from datetime import datetime, timedelta
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

# قیمت‌ها
PRICE_DIVINE = 150
PRICE_CELESTIAL = 299
PRICE_LEGENDARY = 499
PRICE_KINGS_LUCK = 199

# دیتابیس‌های موقت (در تولید واقعی از Redis یا DB استفاده کن)
REFERRALS = {}  # {user_id: count}
DAILY_FREE = {}  # {user_id: {"count": int, "date": str}}
HALL_OF_FAME = []  # list of dicts
VIP_CODES = set()

VIP_FILE = "vip_codes.txt"
if os.path.exists(VIP_FILE):
    with open(VIP_FILE, "r") as f:
        VIP_CODES = set(line.strip().upper() for line in f if line.strip())

def save_vip_codes():
    with open(VIP_FILE, "w") as f:
        f.write("\n".join(sorted(VIP_CODES)))

async def send_certificate(uid, burden, level="Eternal", photo_path=None):
    path, style = create_certificate(uid, burden, level, photo_path)
    if not path:
        await bot.send_message(uid, "The Void is temporarily silent. Try again later.")
        return

    caption = (
        "🔱 <b>ASCENSION COMPLETE</b>\n\n"
        f"\"<i>{burden.upper()}</i>\"\n\n"
        f"<b>Level: {level}</b>\n"
        f"<b>Style: {style}</b>\n\n"
        "Your soul has been eternally crowned in glory.\n"
        "A unique masterpiece, forever preserved.\n"
        f"Holder ID: <code>{uid}</code>\n"
        "2025.VO-ID"
    )
    await bot.send_document(uid, FSInputFile(path), caption=caption, parse_mode="HTML")
    os.remove(path)
    if photo_path and os.path.exists(photo_path):
        os.remove(photo_path)

    # اضافه به Hall of Fame اگر سطح بالا باشه
    if level in ["Celestial", "Legendary"]:
        HALL_OF_FAME.append({"user_id": uid, "burden": burden, "level": level, "style": style, "date": datetime.now().isoformat()})
        if len(HALL_OF_FAME) > 50:
            HALL_OF_FAME = HALL_OF_FAME[-50:]

# /start
@dp.message(F.text == "/start")
async def start(message: types.Message, raw_payload: str = None):
    ref_id = None
    if raw_payload and raw_payload.startswith("ref_"):
        ref_id = int(raw_payload[4:])
        if ref_id != message.from_user.id:
            REFERRALS[ref_id] = REFERRALS.get(ref_id, 0) + 1

    welcome = """
🌌 <b>WELCOME TO THE ETERNAL VOID</b> 🌌

Two paths to ascension:

<b>• Free (3 daily)</b>: Send your burden title
<b>• Divine+ (paid)</b>: Use the portal below for photo + royal styles

Your referral link:
<code>https://t.me/{bot_username}?start=ref_{message.from_user.id}</code>

Bring 5 souls → 50% eternal discount on all purchases
    """.strip()

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔱 ENTER THE VOID", web_app=WebAppInfo(url=f"{os.getenv('WEBHOOK_URL')}/static/index.html"))
    ]])

    await message.answer(welcome, reply_markup=kb, parse_mode="HTML")

# ادمین دستورات
@dp.message(Command("divine"), F.from_user.id == ADMIN_ID)
async def admin_divine(message: types.Message):
    args = message.text.split(maxsplit=1)
    burden = args[1].strip()[:50] if len(args) > 1 else "Admin Divine Creation"
    await message.answer("👑 Admin Divine Forging...")
    await send_certificate(message.from_user.id, burden, "Legendary")

@dp.message(F.photo, F.from_user.id == ADMIN_ID)
async def admin_photo(message: types.Message):
    burden = message.caption.strip()[:50] if message.caption else "Admin Divine Portrait"
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    path = f"admin_{message.from_user.id}.jpg"
    await bot.download_file(file.file_path, path)
    await message.answer("👑 Admin Divine with Portrait Forging...")
    await send_certificate(message.from_user.id, burden, "Legendary", path)

# رایگان
@dp.message(F.text, ~F.text.startswith("/"))
async def free(message: types.Message):
    today = datetime.now().date().isoformat()
    user_data = DAILY_FREE.get(message.from_user.id, {"count": 0, "date": today})
    if user_data["date"] != today:
        user_data = {"count": 0, "date": today}
    
    if user_data["count"] >= 3:
        await message.answer("You have reached your 3 free ascensions today. Return tomorrow or use the portal for Divine.")
        return
    
    burden = message.text.strip()[:50]
    user_data["count"] += 1
    DAILY_FREE[message.from_user.id] = user_data
    
    await message.answer("🌌 Forging your Eternal certificate...")
    await send_certificate(message.from_user.id, burden, "Eternal")

# پرداخت وب‌اپ
async def create_invoice_logic(data):
    uid = data['u']
    burden = data.get('b', 'Eternal Sovereign')
    type = data['type']
    
    # چک VIP
    if burden.upper() in VIP_CODES:
        VIP_CODES.discard(burden.upper())
        save_vip_codes()
        await send_certificate(uid, burden, "Legendary")
        return {"free": True}
    
    # چک رفرال تخفیف
    ref_count = REFERRALS.get(uid, 0)
    discount = 0.5 if ref_count >= 5 else 1.0
    
    prices = {
        "divine": PRICE_DIVINE,
        "celestial": PRICE_CELESTIAL,
        "legendary": PRICE_LEGENDARY,
        "kings-luck": PRICE_KINGS_LUCK
    }
    
    base = prices.get(type, PRICE_DIVINE)
    final = int(base * discount)
    
    # شانس پادشاه
    if type == "kings-luck":
        chance = random.random()
        level = "Eternal"
        if chance < 0.01:
            level = "Legendary"
        elif chance < 0.1:
            level = "Celestial"
        elif chance < 0.4:
            level = "Divine"
        await send_certificate(uid, burden, level)
        return {"free": True}
    
    temp_path = "none"
    if data.get('p'):
        img_data = base64.b64decode(data['p'].split(',')[1])
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        tmp.write(img_data)
        tmp.close()
        temp_path = tmp.name
    
    link = await bot.create_invoice_link(
        title=f"VOID {type.upper()}",
        description="Divine Ascension",
        payload=f"{uid}:{burden}:{temp_path}:{type}",
        currency="XTR",
        prices=[LabeledPrice("Ascension", final)]
    )
    return {"url": link}

@app.post("/create_stars_invoice")
async def invoice(request: Request):
    data = await request.json()
    return await create_invoice_logic(data)

@dp.pre_checkout_query()
async def pre(q: types.PreCheckoutQuery):
    await q.answer(ok=True)

@dp.message(F.successful_payment)
async def paid(message: types.Message):
    parts = message.successful_payment.invoice_payload.split(":")
    uid = int(parts[0])
    burden = parts[1]
    temp_path = parts[2] if parts[2] != "none" else None
    type = parts[3]
    level = {"divine": "Divine", "celestial": "Celestial", "legendary": "Legendary"}.get(type, "Divine")
    await send_certificate(uid, burden, level, temp_path)

# Hall of Fame API
@app.get("/api/hall-of-fame")
async def hall():
    return {"winners": HALL_OF_FAME[-10:]}

app.mount("/static", StaticFiles(directory="static"))

@app.post("/webhook")
async def webhook(request: Request):
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.on_event("startup")
async def startup():
    await bot.set_webhook(f"{os.getenv('WEBHOOK_URL')}/webhook")
