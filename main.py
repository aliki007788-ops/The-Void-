import os
import logging
import json
import requests
import asyncio
from fastapi import FastAPI, Request, BackgroundTasks
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, Update, FSInputFile
from dotenv import load_dotenv

# وارد کردن تابع تولید گواهی
try:
    from cert_gen import create_certificate
except ImportError:
    def create_certificate(uid, burden): return None # برای جلوگیری از کرش در صورت نبود فایل

load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
CRYPTO_TOKEN = os.getenv("CRYPTO_PAY_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
app = FastAPI()

logging.basicConfig(level=logging.INFO)

# --- مدیریت تعاملات تلگرام ---

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🔱 ENTER THE VOID", 
            web_app=WebAppInfo(url=f"{WEBHOOK_URL}/static/index.html")
        )
    ]])
    await message.answer(
        "<b>THE VOID IS WAITING.</b>\n\n"
        "Your burdens are about to become cosmic dust.\n"
        "Click below to begin the ritual.",
        reply_markup=markup, parse_mode="HTML"
    )

@dp.message(lambda message: message.web_app_data is not None)
async def handle_webapp_data(message: types.Message):
    """دریافت داده از مینی‌اپ و ایجاد فاکتور کریپتو"""
    data = json.loads(message.web_app_data.data)
    burden = data.get("need", "Something")
    
    # ساخت فاکتور در کریپتو بات
    headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
    payload = {
        "asset": "USDT",
        "amount": "1.00",
        "description": f"The Void: Sacrificing {burden}",
        "payload": f"{message.from_user.id}:{burden}",
        "paid_btn_name": "openBot",
        "paid_btn_url": f"https://t.me/{(await bot.get_me()).username}"
    }
    
    try:
        res = requests.post("https://pay.cryptotextnet.me/api/createInvoice", headers=headers, json=payload).json()
        if res['ok']:
            pay_url = res['result']['pay_url']
            btn = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="💳 PAY $1 TO REBORN", url=pay_url)
            ]])
            await message.answer(
                f"Ritual initiated for: <b>{burden}</b>\n"
                "To complete the atomization, proceed with the payment.",
                reply_markup=btn, parse_mode="HTML"
            )
    except Exception as e:
        logging.error(f"Invoice error: {e}")

# --- بخش وب‌هوک و اتوماسیون پرداخت ---

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

@app.post("/webhook")
async def telegram_webhook(request: Request):
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.post("/pay_callback")
async def payment_webhook(request: Request, bg_tasks: BackgroundTasks):
    """تایید خودکار پرداخت و ارسال گواهی و وویس"""
    data = await request.json()
    
    # استخراج داده‌ها بر اساس فرمت Crypto Pay
    status = data.get('update_type') or data.get('status')
    if status in ['invoice_paid', 'paid']:
        payload = data.get('payload') or data['request_data'].get('payload')
        user_id, burden = payload.split(":")
        
        # اجرای عملیات نهایی در پس‌زمینه
        bg_tasks.add_task(send_final_reward, user_id, burden)
        
    return {"ok": True}

async def send_final_reward(user_id, burden):
    """ارسال گواهی طلایی + وویس نجوا (صددرصد خودکار)"""
    try:
        # ۱. تولید گواهی
        cert_path = create_certificate(str(user_id), burden)
        
        # ۲. ارسال گواهی
        if cert_path and os.path.exists(cert_path):
            await bot.send_document(
                chat_id=user_id,
                document=FSInputFile(cert_path),
                caption=f"<b>VOID CONFIRMED.</b>\n'{burden}' is gone forever.\nYou are free.",
                parse_mode="HTML"
            )
            os.remove(cert_path) # پاکسازی

        # ۳. ارسال وویس نجوا (The Whisper)
        # نکته: باید فایلی به نام whisper.ogg در پوشه اصلی باشد
        if os.path.exists("whisper.ogg"):
            await bot.send_voice(
                chat_id=user_id,
                voice=FSInputFile("whisper.ogg"),
                caption="🔕 <i>The silence of your rebirth...</i>",
                parse_mode="HTML"
            )

    except Exception as e:
        logging.error(f"Final reward error: {e}")

from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")
