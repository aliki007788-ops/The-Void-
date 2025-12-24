import os
import json
import random
import sqlite3
import base64
import tempfile
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import LabeledPrice, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from cert_gen import create_certificate
from dotenv import load_dotenv

load_dotenv()

# --- پیکربندی اصلی ---
ADMIN_ID = int(os.getenv("ADMIN_ID", "0")) # آیدی عددی خود را در فایل .env وارد کنید
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(storage=MemoryStorage())
app = FastAPI()

SETTINGS_FILE = "settings_void.json"

def get_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {
        "prices": {"Vagabond": 139, "Imperial": 299, "Eternal": 499, "Luck": 249},
        "stats": {"income": 0, "total_nfts": 0}
    }

config = get_settings()

class VoidAdmin(StatesGroup):
    waiting_for_price = State()

# --- دیتابیس ---
def init_db():
    conn = sqlite3.connect("void_core.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS gallery (id INTEGER PRIMARY KEY, dna TEXT, path TEXT, level TEXT, user_id INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, refs INTEGER DEFAULT 0)")
    conn.commit()
    conn.close()

init_db()

# --- پنل مدیریت تلگرام ---
@dp.message(F.text == "/admin", F.from_user.id == ADMIN_ID)
async def admin_main(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 ویرایش قیمت‌ها", callback_data="set_prices")],
        [InlineKeyboardButton(text="📊 آمار حراجی", callback_data="view_auction")]
    ])
    await message.answer("🔱 پنل مدیریت مرکز کنترل خلأ", reply_markup=kb)

@dp.callback_query(F.data == "set_prices", F.from_user.id == ADMIN_ID)
async def ask_price(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("نام پلن و قیمت جدید (مثال: Luck:250):")
    await state.set_state(VoidAdmin.waiting_for_price)

@dp.message(VoidAdmin.waiting_for_price, F.from_user.id == ADMIN_ID)
async def save_price(message: types.Message, state: FSMContext):
    try:
        plan, price = message.text.split(":")
        if plan in config['prices']:
            config['prices'][plan] = int(price)
            with open(SETTINGS_FILE, "w") as f: json.dump(config, f)
            await message.answer(f"✅ قیمت {plan} آپدیت شد.")
        else: await message.answer("❌ پلن نامعتبر.")
    except: await message.answer("❌ فرمت غلط.")
    await state.clear()

# --- API برای وب‌اپ ---
@app.get("/api/config")
async def get_app_config():
    return config["prices"]

@app.post("/api/create_invoice")
async def create_invoice(data: dict):
    uid = data.get('u')
    lvl = data.get('level')
    price = config['prices'].get(lvl, 139)
    
    if lvl == "Luck":
        rnd = random.random() * 100
        if rnd <= 1: lvl = "Legendary"
        elif rnd <= 10: lvl = "Celestial"
        elif rnd <= 40: lvl = "Divine"
        else: lvl = "Eternal"

    payload = f"{uid}:{data['b']}:{lvl}:{data.get('p', 'none')}"
    link = await bot.create_invoice_link(
        title=f"VOID: {lvl}",
        description="Ascending to the void...",
        payload=payload,
        currency="XTR",
        prices=[LabeledPrice(label="Offering", amount=price)]
    )
    return {"url": link}

# --- بخش حیاتی: رفع خطای Not Found ---
# ترتیب قرارگیری این بخش بسیار مهم است. ابتدا فایل‌های استاتیک را سوار می‌کنیم.

# اطمینان از وجود پوشه استاتیک
if not os.path.exists("static"):
    os.makedirs("static")

# سوار کردن پوشه static روی مسیر اصلی /
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# اگر باز هم با آدرس مستقیم مشکل داشتید، این روت را فعال کنید:
@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

# --- اجرای نهایی ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
