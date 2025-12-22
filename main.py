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
        [InlineKeyboardButton(text=f"Market: {'ON' if APP_STATUS['market_enabled'] else 'OFF'}", callback_data="toggle_market")],
        [InlineKeyboardButton(text="👑 Generate Legendary", callback_data="gen_legendary")],
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

@dp.callback_query(F.data == "gen_legendary")
async def gen_legendary(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await send_certificate(callback.from_user.id, "Admin Eternal Creation", "Legendary")
    await callback.answer("Legendary forged!")

# بقیه کد (پرداخت، رایگان، Hall API و ...) مثل نسخه قبلی اما با چک APP_STATUS

app.mount("/static", StaticFiles(directory="static"))

@app.post("/webhook")
async def webhook(request: Request):
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.on_event("startup")
async def startup():
    await bot.set_webhook(f"{os.getenv('WEBHOOK_URL')}/webhook")
