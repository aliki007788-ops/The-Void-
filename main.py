import os
import json
import base64
import tempfile
import random
from datetime import datetime
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

# وضعیت اپ
APP_STATUS = {
    "free_enabled": True,
    "paid_enabled": True,
    "luck_enabled": True,
    "hall_enabled": True,
    "referral_enabled": True,
    "market_enabled": True
}

# دیتابیس
DB = {"users": {}, "hall": [], "market": [], "referrals": {}}
DB_FILE = "void_db.json"
if os.path.exists(DB_FILE):
    DB = json.load(open(DB_FILE))

def save_db():
    json.dump(DB, open(DB_FILE, "w"))

async def send_certificate(uid, burden, level="Eternal", photo_path=None):
    path, style = create_certificate(uid, burden, level, photo_path)
    if not path:
        await bot.send_message(uid, "🌌 The Void is temporarily silent. Try again later.")
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

    if level in ["Celestial", "Legendary"] and APP_STATUS["hall_enabled"]:
        DB["hall"].append({
            "user": f"User_{str(uid)[-4:]}",
            "level": level,
            "burden": burden,
            "style": style,
            "date": datetime.now().isoformat(),
            "path": path  # برای نمایش در Hall
        })
        if len(DB["hall"]) > 50:
            DB["hall"] = DB["hall"][-50:]
        save_db()

# /start
@dp.message(Command("start"))
async def start(message: types.Message):
    payload = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if payload and payload.startswith("ref_"):
        ref_id = int(payload[4:])
        if ref_id != message.from_user.id:
            DB["referrals"][str(ref_id)] = DB["referrals"].get(str(ref_id), 0) + 1
            save_db()

    username = (await bot.get_me()).username

    welcome = f"""
🌌 <b>YOU HAVE ENTERED THE ETERNAL VOID</b> 🌌

The cosmic gates have opened for your soul.

In 2025.VO-ID, burdens become eternal glory.

• <b>Free Eternal</b> (3 daily): Send your burden
• <b>Divine & Legendary</b>: Enter the portal for royal ascension with your image

Your eternal referral link:
<code>https://t.me/{username}?start=ref_{message.from_user.id}</code>

Bring 5 souls → 50% eternal discount forever

One ascension changes you.
Many ascensions change eternity.

The Void calls. Will you answer?
🔱 ENTER THE VOID
    """

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔱 ENTER THE VOID", web_app=WebAppInfo(url=f"{os.getenv('WEBHOOK_URL')}/static/index.html"))
    ]])

    await message.answer(welcome, reply_markup=kb, parse_mode="HTML")

# ادمین پنل
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Free: {'ON' if APP_STATUS['free_enabled'] else 'OFF'}", callback_data="toggle_free")],
        [InlineKeyboardButton(text=f"Paid: {'ON' if APP_STATUS['paid_enabled'] else 'OFF'}", callback_data="toggle_paid")],
        [InlineKeyboardButton(text=f"Luck: {'ON' if APP_STATUS['luck_enabled'] else 'OFF'}", callback_data="toggle_luck")],
        [InlineKeyboardButton(text=f"Hall: {'ON' if APP_STATUS['hall_enabled'] else 'OFF'}", callback_data="toggle_hall")],
        [InlineKeyboardButton(text=f"Market: {'ON' if APP_STATUS['market_enabled'] else 'OFF'}", callback_data="toggle_market")],
        [InlineKeyboardButton(text="👑 Generate Legendary", callback_data="gen_legendary")],
        [InlineKeyboardButton(text="🌌 Generate Celestial", callback_data="gen_celestial")],
        [InlineKeyboardButton(text="💎 Generate Divine", callback_data="gen_divine")],
        [InlineKeyboardButton(text="📊 Stats", callback_data="admin_stats")]
    ])

    await message.answer("👑 VOID Admin Realm", reply_markup=kb)

@dp.callback_query(F.data.startswith("toggle_"))
async def toggle(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    key = callback.data.split("_")[1]
    APP_STATUS[f"{key}_enabled"] = not APP_STATUS[f"{key}_enabled"]
    await admin_panel(callback.message)

@dp.callback_query(F.data.startswith("gen_"))
async def gen_free(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    level_map = {
        "gen_legendary": "Legendary",
        "gen_celestial": "Celestial",
        "gen_divine": "Divine"
    }
    level = level_map.get(callback.data)
    await send_certificate(callback.from_user.id, "Admin Royal Creation", level)
    await callback.answer(f"{level} generated!")

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    stats = f"""
📊 VOID Statistics

Total Users: {len(DB["users"])}
Total Referrals: {sum(DB["referrals"].values())}
Hall Entries: {len(DB["hall"])}
Market Listings: {len(DB["market"])}
    """
    await callback.message.answer(stats)
    await callback.answer()

# رایگان
@dp.message(F.text, ~F.text.startswith("/"))
async def free(message: types.Message):
    if not APP_STATUS["free_enabled"]:
        await message.answer("Free mode is currently disabled.")
        return

    today = datetime.now().date().isoformat()
    user_data = DB["users"].get(str(message.from_user.id), {"count": 0, "date": today})
    if user_data["date"] != today:
        user_data = {"count": 0, "date": today}
    
    if user_data["count"] >= 3:
        await message.answer("🌌 You have reached your 3 free ascensions today.\nUse the portal for Divine ascension.")
        return
    
    burden = message.text.strip()[:50]
    user_data["count"] += 1
    DB["users"][str(message.from_user.id)] = user_data
    save_db()
    
    await message.answer("🌌 Forging your Eternal certificate...")
    await send_certificate(message.from_user.id, burden, "Eternal")

# پرداخت
async def create_invoice_logic(data):
    uid = data['u']
    burden = data.get('b', 'Eternal Sovereign')
    type = data['type']
    
    if not APP_STATUS["paid_enabled"] and type != "kings-luck":
        return {"error": "Paid mode disabled"}
    
    # رفرال تخفیف
    ref_count = DB["referrals"].get(str(uid), 0)
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
    if type == "kings-luck" and APP_STATUS["luck_enabled"]:
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
        description="Ascension to Glory",
        payload=f"{uid}:{burden}:{temp_path}:{type}",
        currency="XTR",
        prices=[LabeledPrice("Ascension Fee", final)]
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

@app.get("/api/hall-of-fame")
async def hall():
    return {"winners": DB["hall"][-10:]}

app.mount("/static", StaticFiles(directory="static"))

@app.post("/webhook")
async def webhook(request: Request):
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.on_event("startup")
async def startup():
    await bot.set_webhook(f"{os.getenv('WEBHOOK_URL')}/webhook")
