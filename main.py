import os
import json
import base64
import tempfile
import random
import time
import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup,
    Update, FSInputFile, LabeledPrice, PreCheckoutQuery,
    SuccessfulPayment
)

from cert_gen import create_certificate, sanitize_burden, validate_image
from dotenv import load_dotenv

load_dotenv()

# ========== CONFIG ==========
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(storage=MemoryStorage())
app = FastAPI(title="THE VOID API")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your-domain.com")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== PRICES ==========
PRICES = {
    "divine": 150,
    "celestial": 299, 
    "legendary": 499,
    "kings_luck": 199
}

# ========== STATUS ==========
APP_STATUS = {
    "free_enabled": True,
    "paid_enabled": True,
    "luck_enabled": True,
    "hall_enabled": True,
    "market_enabled": True
}

# ========== RATE LIMITING ==========
RATE_LIMITS = {}
FREE_TRIES_LIMIT = 3
FREE_TRIES_PERIOD = 24 * 3600  # 24 hours

def check_rate_limit(user_id: int, limit: int = 10, period: int = 60):
    """Rate limiting ساده"""
    current = time.time()
    key = str(user_id)
    
    if key not in RATE_LIMITS:
        RATE_LIMITS[key] = []
    
    # حذف درخواست‌های قدیمی
    RATE_LIMITS[key] = [t for t in RATE_LIMITS[key] if current - t < period]
    
    if len(RATE_LIMITS[key]) >= limit:
        return False
    
    RATE_LIMITS[key].append(current)
    return True

# ========== DATABASE ==========
DB_FILE = "void_db.json"
DB = {
    "users": {},
    "hall": [],
    "market": [],
    "referrals": {},
    "free_tries": {}
}

if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, "r") as f:
            DB.update(json.load(f))
    except:
        pass

def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(DB, f, default=str)

# ========== HELPER FUNCTIONS ==========
def get_user_data(user_id: int):
    """دریافت داده کاربر"""
    uid = str(user_id)
    if uid not in DB["users"]:
        DB["users"][uid] = {
            "burdens": [],
            "certificates": [],
            "referrals": [],
            "discount": 0,
            "created_at": datetime.now().isoformat()
        }
        save_db()
    return DB["users"][uid]

def update_user_data(user_id: int, data: dict):
    """آپدیت داده کاربر"""
    uid = str(user_id)
    DB["users"][uid].update(data)
    save_db()

def add_to_hall(user_id: int, burden: str, level: str):
    """افزودن به تالار مشاهیر"""
    if not APP_STATUS["hall_enabled"]:
        return
    
    hall_entry = {
        "user_id": user_id,
        "username": f"User_{str(user_id)[-4:]}",
        "burden": burden,
        "level": level,
        "date": datetime.now().isoformat()
    }
    
    DB["hall"].append(hall_entry)
    if len(DB["hall"]) > 50:
        DB["hall"] = DB["hall"][-50:]
    
    save_db()

async def safe_send_certificate(user_id: int, burden: str, level: str = "Eternal", photo_path: str = None):
    """ارسال ایمن گواهینامه"""
    try:
        burden = sanitize_burden(burden)
        
        # بررسی عکس
        if photo_path and not validate_image(photo_path):
            photo_path = None
        
        # ایجاد گواهینامه
        cert_path, style = create_certificate(user_id, burden, level, photo_path)
        
        if not cert_path:
            await bot.send_message(user_id, "🌌 The Void creation failed. Try again.")
            return False
        
        # متن کپشن
        caption = (
            f"🔱 <b>ASCENSION COMPLETE</b>\n\n"
            f"\"{burden.upper()}\"\n\n"
            f"<b>Level: {level}</b>\n"
            f"<b>Style: {style}</b>\n\n"
            f"Your eternal masterpiece is ready.\n"
            f"Holder ID: <code>{user_id}</code>\n"
            f"2025.VO-ID"
        )
        
        # ارسال
        await bot.send_document(user_id, FSInputFile(cert_path), caption=caption, parse_mode="HTML")
        
        # حذف فایل‌های موقت
        try:
            if os.path.exists(cert_path):
                os.remove(cert_path)
            if photo_path and os.path.exists(photo_path):
                os.remove(photo_path)
        except:
            pass
        
        # ذخیره در تاریخچه
        user_data = get_user_data(user_id)
        user_data["burdens"].append(burden[:30])
        user_data["certificates"].append({
            "burden": burden,
            "level": level,
            "date": datetime.now().isoformat()
        })
        update_user_data(user_id, user_data)
        
        # افزودن به تالار برای سطوح بالا
        if level in ["Celestial", "Legendary"]:
            add_to_hall(user_id, burden, level)
        
        return True
        
    except Exception as e:
        print(f"Error sending certificate: {e}")
        await bot.send_message(user_id, "❌ Error creating certificate.")
        return False

# ========== BOT COMMANDS ==========
@dp.message(Command("start"))
async def start_command(message: types.Message):
    """دستور /start"""
    # بررسی رفرال
    parts = message.text.split()
    if len(parts) > 1 and parts[1].startswith("ref_"):
        try:
            ref_id = int(parts[1][4:])
            if ref_id != message.from_user.id:
                DB["referrals"][str(ref_id)] = DB["referrals"].get(str(ref_id), 0) + 1
                save_db()
        except:
            pass
    
    # ایجاد پیام خوش‌آمد
    username = (await bot.get_me()).username
    welcome = f"""
🌌 <b>WELCOME TO THE VOID</b> 🌌

Transform your burden into eternal glory.

• <b>Free Eternal</b> (3 daily): Send your burden as text
• <b>Divine & Legendary</b>: Enter portal for paid ascension

Your referral link:
<code>https://t.me/{username}?start=ref_{message.from_user.id}</code>

Invite 5 friends → 50% discount forever
    """
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🔱 ENTER VOID", 
            web_app=WebAppInfo(url=f"{WEBHOOK_URL}/static/index.html")
        )
    ]])
    
    await message.answer(welcome, reply_markup=kb, parse_mode="HTML")

# ========== FREE MODE ==========
@dp.message(F.text & ~F.command)
async def free_mode(message: types.Message):
    """حالت رایگان"""
    if not APP_STATUS["free_enabled"]:
        await message.answer("Free ascensions are currently disabled.")
        return
    
    # Rate limiting
    if not check_rate_limit(message.from_user.id, limit=5, period=60):
        await message.answer("⏳ Please wait before your next request.")
        return
    
    # بررسی تلاش‌های روزانه
    uid = str(message.from_user.id)
    today = datetime.now().date().isoformat()
    
    if uid not in DB["free_tries"]:
        DB["free_tries"][uid] = {"date": today, "count": 0}
    
    tries_data = DB["free_tries"][uid]
    
    # ریست روزانه
    if tries_data["date"] != today:
        tries_data = {"date": today, "count": 0}
    
    if tries_data["count"] >= FREE_TRIES_LIMIT:
        await message.answer("🌌 Daily free tries exhausted. Use portal for paid ascensions.")
        return
    
    # افزایش شمارنده
    tries_data["count"] += 1
    DB["free_tries"][uid] = tries_data
    save_db()
    
    # پردازش burden
    burden = message.text.strip()[:50]
    if not burden:
        await message.answer("Please enter your burden.")
        return
    
    await message.answer("🌀 Forging your Eternal certificate...")
    await safe_send_certificate(message.from_user.id, burden, "Eternal")

# ========== PAYMENT HANDLING ==========
@app.post("/create_stars_invoice")
async def create_invoice(request: Request):
    """ایجاد invoice برای پرداخت"""
    try:
        data = await request.json()
        user_id = data.get("u")
        burden = data.get("b", "Eternal Sovereign")
        item_type = data.get("type")
        
        if not user_id or not item_type:
            return JSONResponse({"error": "Missing parameters"}, status_code=400)
        
        # Rate limiting برای پرداخت
        if not check_rate_limit(user_id, limit=3, period=30):
            return JSONResponse({"error": "Too many requests"}, status_code=429)
        
        # Sanitize burden
        burden = sanitize_burden(burden)
        
        # شانس پادشاه
        if item_type == "kings_luck" and APP_STATUS["luck_enabled"]:
            chance = random.random()
            if chance < 0.01:
                level = "Legendary"
            elif chance < 0.1:
                level = "Celestial"
            elif chance < 0.4:
                level = "Divine"
            else:
                level = "Eternal"
            
            # ذخیره burden کاربر
            user_data = get_user_data(user_id)
            user_data["burdens"].append(burden[:30])
            update_user_data(user_id, user_data)
            
            # ایجاد گواهینامه
            await safe_send_certificate(user_id, burden, level)
            return JSONResponse({"free": True, "level": level})
        
        # محاسبه قیمت با تخفیف
        base_price = PRICES.get(item_type, PRICES["divine"])
        ref_count = DB["referrals"].get(str(user_id), 0)
        discount = 0.5 if ref_count >= 5 else 1.0
        final_price = int(base_price * discount)
        
        # پردازش عکس
        temp_path = None
        if data.get("p"):
            try:
                # حذف header base64
                img_data = base64.b64decode(data["p"].split(",")[1])
                
                # بررسی سایز
                if len(img_data) > 5 * 1024 * 1024:  # 5MB
                    return JSONResponse({"error": "Image too large"}, status_code=400)
                
                # ذخیره موقت
                temp_path = f"temp_{user_id}_{int(time.time())}.jpg"
                with open(temp_path, "wb") as f:
                    f.write(img_data)
            except:
                temp_path = None
        
        # ایجاد لینک پرداخت
        invoice_url = await bot.create_invoice_link(
            title=f"VOID {item_type.upper()} ASCENSION",
            description=f"Eternal certificate: {burden}",
            payload=f"{user_id}:{burden}:{temp_path or 'none'}:{item_type}",
            provider_token=os.getenv("PROVIDER_TOKEN"),
            currency="XTR",
            prices=[LabeledPrice(label="Ascension", amount=final_price)]
        )
        
        return JSONResponse({"url": invoice_url})
        
    except Exception as e:
        print(f"Invoice error: {e}")
        return JSONResponse({"error": "Internal error"}, status_code=500)

@dp.pre_checkout_query()
async def pre_checkout_handler(query: PreCheckoutQuery):
    """قبل از پرداخت"""
    await query.answer(ok=True)

@dp.message(F.successful_payment)
async def successful_payment_handler(message: types.Message):
    """پرداخت موفق"""
    payload = message.successful_payment.invoice_payload.split(":")
    
    if len(payload) != 4:
        await message.answer("❌ Payment error. Contact support.")
        return
    
    user_id = int(payload[0])
    burden = payload[1]
    photo_path = None if payload[2] == "none" else payload[2]
    item_type = payload[3]
    
    # تعیین سطح بر اساس نوع
    level_map = {
        "divine": "Divine",
        "celestial": "Celestial", 
        "legendary": "Legendary"
    }
    level = level_map.get(item_type, "Divine")
    
    # ایجاد و ارسال گواهینامه
    await message.answer("🌀 Forging your paid ascension...")
    success = await safe_send_certificate(user_id, burden, level, photo_path)
    
    if success:
        await message.answer("✨ Ascension complete! Check your certificate.")
    else:
        await message.answer("❌ Error. Contact support for refund.")

# ========== ADMIN PANEL ==========
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    """پنل ادمین"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Access denied.")
        return
    
    stats = f"""
👑 VOID ADMIN PANEL

Users: {len(DB['users'])}
Referrals: {sum(DB['referrals'].values())}
Hall entries: {len(DB['hall'])}
Free tries today: {sum(d.get('count', 0) for d in DB['free_tries'].values())}
    """
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"Free: {'ON' if APP_STATUS['free_enabled'] else 'OFF'}", callback_data="toggle_free"),
            InlineKeyboardButton(text=f"Paid: {'ON' if APP_STATUS['paid_enabled'] else 'OFF'}", callback_data="toggle_paid")
        ],
        [
            InlineKeyboardButton(text=f"Luck: {'ON' if APP_STATUS['luck_enabled'] else 'OFF'}", callback_data="toggle_luck"),
            InlineKeyboardButton(text=f"Hall: {'ON' if APP_STATUS['hall_enabled'] else 'OFF'}", callback_data="toggle_hall")
        ],
        [
            InlineKeyboardButton(text="👑 Gen Legendary", callback_data="gen_legendary"),
            InlineKeyboardButton(text="📊 Stats", callback_data="admin_stats")
        ]
    ])
    
    await message.answer(stats, reply_markup=kb)

@dp.callback_query(F.data.startswith("toggle_"))
async def toggle_feature(callback: types.CallbackQuery):
    """تغییر وضعیت ویژگی‌ها"""
    if callback.from_user.id != ADMIN_ID:
        return
    
    feature = callback.data.split("_")[1]
    if f"{feature}_enabled" in APP_STATUS:
        APP_STATUS[f"{feature}_enabled"] = not APP_STATUS[f"{feature}_enabled"]
        await callback.answer(f"Feature {feature} toggled")
        await admin_panel(callback.message)

@dp.callback_query(F.data.startswith("gen_"))
async def generate_admin(callback: types.CallbackQuery):
    """تولید گواهینامه توسط ادمین"""
    if callback.from_user.id != ADMIN_ID:
        return
    
    level_map = {
        "gen_legendary": "Legendary",
        "gen_celestial": "Celestial",
        "gen_divine": "Divine"
    }
    
    level = level_map.get(callback.data)
    if level:
        await safe_send_certificate(callback.from_user.id, "Admin Creation", level)
        await callback.answer(f"{level} created!")

# ========== API ENDPOINTS ==========
@app.get("/api/hall-of-fame")
async def get_hall():
    """دریافت تالار مشاهیر"""
    return JSONResponse({
        "winners": DB["hall"][-10:],  # آخرین ۱۰ تا
        "total": len(DB["hall"])
    })

@app.get("/api/user/{user_id}")
async def get_user_info(user_id: int):
    """دریافت اطلاعات کاربر"""
    user_data = get_user_data(user_id)
    return JSONResponse({
        "referrals": DB["referrals"].get(str(user_id), 0),
        "discount": 50 if DB["referrals"].get(str(user_id), 0) >= 5 else 0,
        "burdens": user_data.get("burdens", [])[-5:],  # آخرین ۵ تا
        "certificates": len(user_data.get("certificates", []))
    })

# ========== STATIC FILES ==========
app.mount("/static", StaticFiles(directory="static"), name="static")

# ========== WEBHOOK ==========
@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Webhook تلگرام"""
    try:
        update_data = await request.json()
        update = Update.model_validate(update_data, context={"bot": bot})
        await dp.feed_update(bot, update)
        return {"ok": True}
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"ok": False, "error": str(e)}

# ========== STARTUP ==========
@app.on_event("startup")
async def startup():
    """شروع برنامه"""
    # تنظیم webhook
    await bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    
    # ایجاد پوشه‌ها
    Path("static").mkdir(exist_ok=True)
    Path("temp").mkdir(exist_ok=True)
    
    print("🌌 THE VOID is running...")

@app.on_event("shutdown")
async def shutdown():
    """خاموشی برنامه"""
    await bot.session.close()
    save_db()
    print("🌌 THE VOID stopped.")

# ========== MAIN ==========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
