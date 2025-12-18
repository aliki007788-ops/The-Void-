import os
import logging
import json
import requests
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, Update, FSInputFile
from dotenv import load_dotenv

# وارد کردن تابع تولید گواهی جدید
from cert_gen import create_certificate

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
            text="🔱 ASCEND TO THE VOID", 
            web_app=WebAppInfo(url=f"{WEBHOOK_URL}/static/index.html")
        )
    ]])
    await message.answer(
        "<b>THE VOID IS CALLING.</b>\n\n"
        "Your burdens are about to become cosmic stardust.\n"
        "Enter the ritual below to begin your ascension.",
        reply_markup=markup, parse_mode="HTML"
    )

@dp.message(lambda message: message.web_app_data is not None)
async def handle_webapp_data(message: types.Message):
    """دریافت داده از مینی‌اپ و ایجاد فاکتور کریپتو"""
    data = json.loads(message.web_app_data.data)
    burden = data.get("need", "The Unnamed")
    
    # ساخت فاکتور در کریپتو بات
    headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
    payload = {
        "asset": "USDT",
        "amount": "1.00",
        "description": f"The Void: Atomizing {burden}",
        "payload": f"{message.from_user.id}:{burden}",
        "paid_btn_name": "openBot",
        "paid_btn_url": f"https://t.me/{(await bot.get_me()).username}"
    }
    
    try:
        # آدرس تست یا اصلی درگاه را چک کنید (pay.cryptotextnet.me برای تست یا اصلی)
        res = requests.post("https://pay.cryptotextnet.me/api/createInvoice", headers=headers, json=payload).json()
        if res['ok']:
            pay_url = res['result']['pay_url']
            btn = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="💳 MINT YOUR PROOF ($1)", url=pay_url)
            ]])
            await message.answer(
                f"Ritual for <b>{burden}</b> is synchronized.\n"
                "To finalize the transition to the blockchain, proceed with the minting.",
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
    """تایید خودکار پرداخت و ارسال گواهی NFT-Style"""
    data = await request.json()
    status = data.get('update_type') or data.get('status')
    
    if status in ['invoice_paid', 'paid']:
        payload = data.get('payload') or data.get('request_data', {}).get('payload')
        if payload:
            user_id, burden = payload.split(":")
            bg_tasks.add_task(send_final_reward, user_id, burden)
    return {"ok": True}

async def send_final_reward(user_id, burden):
    """ارسال گواهی لوکس + وویس نجوا (صددرصد خودکار)"""
    try:
        # ۱. تولید گواهی با استایل جدید (مربع و NFT)
        cert_path = create_certificate(str(user_id), burden)
        
        # ۲. ارسال گواهی
        if cert_path and os.path.exists(cert_path):
            caption = (
                f"🔱 **TRANSACTION COMPLETE**\n\n"
                f"The burden of '{burden}' has been converted into a unique digital asset.\n"
                f"Your proof of ascension is now registered."
            )
            await bot.send_document(
                chat_id=user_id,
                document=FSInputFile(cert_path),
                caption=caption,
                parse_mode="Markdown"
            )
            os.remove(cert_path)

        # ۳. ارسال وویس نجوا (مطمئن شو فایل whisper.ogg در پوشه اصلی هست)
        voice_file = "whisper.ogg"
        if os.path.exists(voice_file):
            await bot.send_voice(
                chat_id=user_id,
                voice=FSInputFile(voice_file),
                caption="🔕 *The Void whispers back to you...*",
                parse_mode="Markdown"
            )

    except Exception as e:
        logging.error(f"Final reward error: {e}")

app.mount("/static", StaticFiles(directory="static"), name="static")
