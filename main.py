import os
import json
import random
import sqlite3
import base64
import tempfile
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import LabeledPrice, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from cert_gen import create_certificate  # اتصال به موتور هوش مصنوعی شما
from dotenv import load_dotenv

load_dotenv()

# --- تنظیمات اولیه ---
app = FastAPI()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# قیمت‌ها به ستاره تلگرام
PRICES = {
    "Vagabond": 70,
    "Imperial": 120,
    "Eternal": 250,
    "Luck": 30
}

# --- بخش مدیریت دیتابیس (SQLite) ---
def init_db():
    conn = sqlite3.connect("void_database.db")
    c = conn.cursor()
    # جدول کاربران و رفرال‌ها
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, referrals INTEGER DEFAULT 0, invited_by INTEGER)''')
    # جدول تالار افتخارات (ذخیره مسیر فایل‌ها و DNA)
    c.execute('''CREATE TABLE IF NOT EXISTS gallery 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, dna TEXT, 
                  path TEXT, level TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# --- منطق محاسباتی شانس پادشاه (بر اساس درصدهای اعلامی شما) ---
def get_luck_level():
    chance = random.random() * 100
    if chance <= 1:
        return "Legendary"  # ۱ درصد فوق حرفه‌ای
    elif chance <= 10:
        return "Celestial"  # ۹ درصد (۱۰ - ۱)
    elif chance <= 40:
        return "Divine"     # ۳۰ درصد (۴۰ - ۱۰)
    else:
        return "Eternal"    # ۶۰ درصد باقی‌مانده

# --- API‌های مورد نیاز فرانت‌اِند (WebApp) ---

@app.get("/api/init/{user_id}")
async def init_app(user_id: int):
    """دریافت اطلاعات اولیه رفرال و تصاویر تالار افتخارات"""
    conn = sqlite3.connect("void_database.db")
    c = conn.cursor()
    
    # تعداد رفرال کاربر
    c.execute("SELECT referrals FROM users WHERE user_id = ?", (user_id,))
    res = c.fetchone()
    ref_count = res[0] if res else 0
    
    # دریافت ۶۰ تصویر برتر آخر برای تالار
    c.execute("SELECT path, level, dna FROM gallery ORDER BY id DESC LIMIT 60")
    top_60 = [{"path": r[0], "level": r[1], "dna": r[2]} for r in c.fetchall()]
    
    conn.close()
    return {"ref_count": ref_count, "top_60": top_60}

@app.post("/api/create_invoice")
async def create_invoice(data: dict):
    """ایجاد فاکتور پرداخت ستاره تلگرام"""
    uid = data.get('u')
    burden = data.get('b')
    level = data.get('level')
    photo_b64 = data.get('p')  # عکس آپلود شده کاربر

    # تعیین سطح و قیمت نهایی
    final_level = level
    if level == "Luck":
        final_level = get_luck_level()
        amount = PRICES["Luck"]
    else:
        amount = PRICES.get(level, 70)

    # بررسی رفرال ۶ تایی (اگر ۶ دعوت داشت، رایگان می‌شود)
    conn = sqlite3.connect("void_database.db")
    c = conn.cursor()
    c.execute("SELECT referrals FROM users WHERE user_id = ?", (uid,))
    refs = c.fetchone()[0] if c.fetchone() else 0
    
    if refs >= 6:
        # اینجا رفرال صفر می‌شود و مستقیم به تولید تصویر می‌رود
        c.execute("UPDATE users SET referrals = 0 WHERE user_id = ?", (uid,))
        conn.commit()
        conn.close()
        return {"free": True, "level": final_level}
    
    conn.close()

    # ذخیره موقت عکس آپلود شده برای استفاده بعد از پرداخت
    temp_path = "none"
    if photo_b64:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(base64.b64decode(photo_b64.split(",")[1]))
            temp_path = tmp.name

    # ایجاد لینک پرداخت ستاره
    invoice_payload = f"{uid}:{burden}:{final_level}:{temp_path}"
    link = await bot.create_invoice_link(
        title=f"VOID ASCENSION - {final_level.upper()}",
        description=f"Sacrificing: {burden[:50]}...",
        payload=invoice_payload,
        currency="XTR",
        prices=[LabeledPrice(label="Offering", amount=amount)]
    )
    return {"url": link}

# --- هندلرهای تلگرام (Bot Logic) ---

@dp.message(F.text.startswith("/start"))
async def start_handler(message: types.Message):
    """مدیریت شروع ربات و سیستم زیرمجموعه‌گیری"""
    uid = message.from_user.id
    args = message.text.split()
    
    conn = sqlite3.connect("void_database.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (uid,))
    
    # اگر با لینک رفرال وارد شده باشد
    if len(args) > 1 and args[1].isdigit():
        inviter_id = int(args[1])
        if inviter_id != uid:
            c.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id = ?", (inviter_id,))
    
    conn.commit()
    conn.close()

    web_url = os.getenv("WEBAPP_URL")
    markup = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="ENTER THE VOID 🌀", web_app=WebAppInfo(url=web_url))
    ]])
    await message.answer("🔱 WELCOME TO THE VOID\nYour soul is ready for ascension.", reply_markup=markup)

@dp.pre_checkout_query()
async def checkout_handler(query: types.PreCheckoutQuery):
    await query.answer(ok=True)

@dp.message(F.successful_payment)
async def payment_success(message: types.Message):
    """بعد از پرداخت موفق، تصویر تولید و در تالار ثبت می‌شود"""
    payload = message.successful_payment.invoice_payload
    uid, burden, level, temp_path = payload.split(":")
    
    # فراخوانی تابع تولید تصویر از فایل cert_gen.py
    # اگر temp_path وجود داشت، به عنوان عکس ورودی داده می‌شود
    photo_in = None if temp_path == "none" else temp_path
    
    file_path, dna = create_certificate(int(uid), burden, level, photo_in)

    # ثبت در دیتابیس تالار افتخارات
    conn = sqlite3.connect("void_database.db")
    c = conn.cursor()
    c.execute("INSERT INTO gallery (user_id, dna, path, level) VALUES (?, ?, ?, ?)",
              (uid, dna, file_path, level))
    conn.commit()
    conn.close()

    # ارسال تصویر نهایی برای کاربر
    await message.answer_photo(
        photo=types.FSInputFile(file_path),
        caption=f"🔱 ASCENSION COMPLETE\nLevel: {level}\nDNA: {dna}\n\nYour soul is now eternal in the Hall of Fame."
    )

# اتصال فرانت‌اِند به سرور
app.mount("/", StaticFiles(directory="static", html=True), name="static")
