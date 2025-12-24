import os
import json
import random
import sqlite3
import base64
import tempfile
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import LabeledPrice, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from cert_gen import create_certificate
from dotenv import load_dotenv

load_dotenv()

# --- تنظیمات سیستمی ---
ADMIN_ID = int(os.getenv("ADMIN_ID", "آیدی_عددی_تلگرام_شما")) # حتما آیدی خود را بگذارید
bot = Bot(token=os.getenv("BOT_TOKEN"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
app = FastAPI()

# فایل ذخیره تنظیمات برای ماندگاری قیمت‌ها
SETTINGS_FILE = "settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {
        "prices": {"Vagabond": 139, "Imperial": 299, "Eternal": 499, "Luck": 249},
        "stats": {"total_stars": 0, "total_ascensions": 0}
    }

def save_settings(data):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f)

settings = load_settings()

# --- کلاس حالات ادمین (FSM) ---
class AdminStates(StatesGroup):
    waiting_for_price = State()
    waiting_for_vip = State()
    waiting_for_manual_gen = State()

# --- دیتابیس ---
def init_db():
    conn = sqlite3.connect("void_pro.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, refs INTEGER DEFAULT 0)")
    c.execute("CREATE TABLE IF NOT EXISTS gallery (path TEXT, dna TEXT, level TEXT, user_id INTEGER)")
    conn.commit()
    conn.close()

init_db()

# --- منوی مدیریت (فارسی) ---
def get_admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 ویرایش قیمت‌ها", callback_data="adm_prices")],
        [InlineKeyboardButton(text="📊 آمار و دخل", callback_data="adm_stats")],
        [InlineKeyboardButton(text="🎁 صدور گواهینامه رایگان (ادمین)", callback_data="adm_free_gen")],
        [InlineKeyboardButton(text="🧹 پاکسازی گالری", callback_data="adm_clear_hall")]
    ])

# --- هندلرهای بخش ادمین ---

@dp.message(F.text == "/admin", F.from_user.id == ADMIN_ID)
async def admin_panel(message: types.Message):
    await message.answer("🔱 به مرکز کنترل خلأ خوش آمدید، عالیجناب.", reply_markup=get_admin_kb())

@dp.callback_query(F.data == "adm_prices", F.from_user.id == ADMIN_ID)
async def view_prices(callback: types.CallbackQuery):
    p = settings['prices']
    text = f"قیمت‌های فعلی:\nVagabond: {p['Vagabond']}\nImperial: {p['Imperial']}\nEternal: {p['Eternal']}\nLuck: {p['Luck']}\n\nبرای تغییر، نام پلن و قیمت را بفرستید (مثال: Luck:200)"
    await callback.message.edit_text(text, reply_markup=get_admin_kb())
    await dp.fsm.get_context(callback.message).set_state(AdminStates.waiting_for_price)

@dp.message(AdminStates.waiting_for_price, F.from_user.id == ADMIN_ID)
async def update_price_logic(message: types.Message, state: FSMContext):
    try:
        plan, price = message.text.split(":")
        if plan in settings['prices']:
            settings['prices'][plan] = int(price)
            save_settings(settings)
            await message.answer(f"✅ قیمت {plan} به {price} تغییر یافت.")
        else:
            await message.answer("❌ نام پلن اشتباه است.")
    except:
        await message.answer("❌ فرمت اشتباه. مثال: Vagabond:150")
    await state.clear()

@dp.callback_query(F.data == "adm_stats", F.from_user.id == ADMIN_ID)
async def show_stats(callback: types.CallbackQuery):
    s = settings['stats']
    text = f"📊 آمار کل:\n✨ مجموع ستاره‌ها: {s['total_stars']}\n🔥 تعداد صعودها: {s['total_ascensions']}"
    await callback.message.edit_text(text, reply_markup=get_admin_kb())

# --- منطق اصلی برنامه (API) ---

@app.post("/api/create_invoice")
async def create_invoice(data: dict):
    uid = data.get('u')
    level = data.get('level')
    price = settings['prices'].get(level, 139)
    
    # منطق شانس پادشاه (۶۰-۳۰-۹-۱)
    final_level = level
    if level == "Luck":
        chance = random.random() * 100
        if chance <= 1: final_level = "Legendary"
        elif chance <= 10: final_level = "Celestial"
        elif chance <= 40: final_level = "Divine"
        else: final_level = "Eternal"

    payload = f"{uid}:{data['b']}:{final_level}:{data.get('p', 'none')}"
    link = await bot.create_invoice_link(
        title=f"ASCENSION: {final_level}",
        description="Fading into the void...",
        payload=payload,
        currency="XTR",
        prices=[LabeledPrice(label="Offering", amount=price)]
    )
    return {"url": link}

@dp.message(F.successful_payment)
async def on_payment(message: types.Message):
    # آپدیت آمار بعد از پرداخت
    settings['stats']['total_stars'] += message.successful_payment.total_amount
    settings['stats']['total_ascensions'] += 1
    save_settings(settings)
    
    # تولید تصویر (در اینجا تابع cert_gen فراخوانی می‌شود)
    # ... کدهای مربوط به ارسال فایل برای کاربر
    await message.answer("🔱 پرداخت تایید شد. روح شما در حال صعود است...")

# --- اجرای وب‌اپ و سرور ---
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
