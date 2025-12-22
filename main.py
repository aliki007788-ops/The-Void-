import os
import json
import base64
import tempfile
import random
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, Update, FSInputFile, LabeledPrice
from aiogram.filters import Command
from cert_gen import create_certificate
from dotenv import load_dotenv

load_dotenv()

# تنظیمات
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# قیمت‌ها طبق دستور شما
PRICES = {
    "divine": 150,
    "kings-luck": 199,
    "celestial": 299,
    "legendary": 499
}

# دیتابیس ساده JSON
DB_FILE = "void_db.json"
DB = {"users": {}, "hall": [], "market": [], "referrals": {}}
if os.path.exists(DB_FILE):
    try: DB = json.load(open(DB_FILE))
    except: pass

def save_db():
    json.dump(DB, open(DB_FILE, "w"))

# ربات و سرور
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# --- توابع اصلی ---

async def finalize_ascension(user_id, burden, level, photo_path=None):
    """تولید نهایی و ارسال گواهی"""
    path, style_name = create_certificate(user_id, burden, level, photo_path)
    
    if not path:
        await bot.send_message(user_id, "⚠️ The Void is silent. Please try again.")
        return

    # ذخیره در تاریخچه
    uid_str = str(user_id)
    if uid_str not in DB["users"]: DB["users"][uid_str] = {"history": []}
    DB["users"][uid_str]["history"].append({"level": level, "date": str(datetime.now())})
    
    # افزودن به تالار افتخارات (فقط رده‌های بالا)
    if level in ["Legendary", "Celestial"]:
        entry = {
            "user": f"Soul-{uid_str[-4:]}",
            "level": level,
            "burden": burden,
            "style": style_name,
            "date": str(datetime.now())
        }
        DB["hall"].insert(0, entry) # جدیدترین اول
        if len(DB["hall"]) > 50: DB["hall"] = DB["hall"][:50]
        save_db()

    caption = (
        f"🔱 <b>ASCENSION COMPLETE</b>\n\n"
        f"\"<i>{burden.upper()}</i>\"\n\n"
        f"<b>Rank:</b> {level.upper()}\n"
        f"<b>Style:</b> {style_name}\n"
        f"<b>Void ID:</b> <code>{user_id}</code>"
    )
    
    await bot.send_document(user_id, FSInputFile(path), caption=caption, parse_mode="HTML")
    
    # پاکسازی فایل موقت
    try: 
        os.remove(path)
        if photo_path: os.remove(photo_path)
    except: pass

# --- هندلرهای تلگرام ---

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    # لاجیک رفرال
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        ref = args[1][4:]
        if ref != str(message.from_user.id):
            DB["referrals"][ref] = DB["referrals"].get(ref, 0) + 1
            save_db()

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔱 ENTER THE VOID", web_app=WebAppInfo(url=f"{WEBHOOK_URL}/static/index.html"))
    ]])
    
    await message.answer(
        "🌌 <b>WELCOME TO THE VOID</b>\n\n"
        "Sacrifice your burden. Receive eternal glory.\n\n"
        "• <b>Free:</b> Eternal Grade (3x Daily)\n"
        "• <b>Divine:</b> Royal Grade (150 ⭐)\n"
        "• <b>King's Luck:</b> Risk it all (199 ⭐)\n"
        "• <b>Legendary:</b> Ultimate Grade (499 ⭐)\n\n"
        "<i>Open the portal below...</i>",
        reply_markup=kb, parse_mode="HTML"
    )

@app.post("/create_stars_invoice")
async def create_invoice(request: Request):
    data = await request.json()
    uid = data.get('u')
    burden = data.get('b', 'Burden')
    plan = data.get('type') # free, divine, celestial, legendary, kings-luck
    photo = data.get('p')

    # 1. حالت رایگان (محدودیت 3 بار در روز)
    if plan == 'free':
        today = str(datetime.now().date())
        user_data = DB["users"].get(str(uid), {})
        daily = user_data.get("daily_limit", {"date": today, "count": 0})
        
        if daily["date"] != today: daily = {"date": today, "count": 0}
        
        if daily["count"] >= 3:
            return {"error": "Daily limit reached"}
        
        daily["count"] += 1
        user_data["daily_limit"] = daily
        DB["users"][str(uid)] = user_data
        save_db()
        
        # تولید مستقیم
        await finalize_ascension(uid, burden, "Eternal")
        return {"free": True}

    # 2. پردازش عکس برای حالت‌های پولی
    temp_path = "none"
    if photo:
        try:
            head, encoded = photo.split(",", 1)
            file_bytes = base64.b64decode(encoded)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(file_bytes)
                temp_path = tmp.name
        except: pass

    # 3. ایجاد لینک پرداخت
    amount = PRICES.get(plan, 150)
    title = f"VOID {plan.upper()}"
    desc = "Ascension Fee"
    
    if plan == "kings-luck":
        title = "KING'S LUCK"
        desc = "Risk for Legendary Status"

    link = await bot.create_invoice_link(
        title=title,
        description=desc,
        payload=f"{uid}:{plan}:{temp_path}:{burden}",
        currency="XTR",
        prices=[LabeledPrice(label="Stars", amount=amount)]
    )
    return {"url": link}

@dp.message(F.successful_payment)
async def payment_success(message: types.Message):
    payload = message.successful_payment.invoice_payload
    uid, plan, path, burden = payload.split(":", 3)
    uid = int(uid)
    real_path = None if path == "none" else path
    
    final_rank = "Divine" # پیش فرض
    
    if plan == "celestial": final_rank = "Celestial"
    elif plan == "legendary": final_rank = "Legendary"
    elif plan == "kings-luck":
        # لاجیک شانس: 10% Legendary, 30% Celestial, 60% Divine
        roll = random.random()
        if roll < 0.10: final_rank = "Legendary"
        elif roll < 0.40: final_rank = "Celestial"
        else: final_rank = "Divine"

    await bot.send_message(uid, f"✨ Payment Accepted. Forging {final_rank}...")
    await finalize_ascension(uid, burden, final_rank, real_path)

# --- اجرا ---
app.mount("/static", StaticFiles(directory="static"))

@app.post("/webhook")
async def webhook(request: Request):
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(f"{WEBHOOK_URL}/webhook")
