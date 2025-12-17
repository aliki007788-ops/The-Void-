import os
import json
import uuid
import requests
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, Update, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F
from cert_gen import create_certificate
from fastapi.staticfiles import StaticFiles

TOKEN = os.getenv("BOT_TOKEN")
CRYPTO_TOKEN = os.getenv("CRYPTO_PAY_TOKEN")
BASE_URL = os.getenv("WEBHOOK_URL")  # مثلاً https://your-project.onrender.com

bot = Bot(token=TOKEN)
dp = Dispatcher()
app = FastAPI()

# ذخیره موقت need برای هر کاربر (در پروداکشن بهتره از Redis یا دیتابیس استفاده کنی)
user_needs = {}

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(url=f"{BASE_URL}/webhook")

@app.post("/webhook")
async def telegram_webhook(request: Request):
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot=bot, update=update)

# هندلر دریافت داده از WebApp (مینی‌اپ جدید با انیمیشن ذرات)
@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message, web_app_data: types.WebAppData):
    try:
        data = json.loads(web_app_data.data)
        if data.get("action") == "create_invoice":
            need = data["need"].strip()
            if not need:
                await message.answer("The Void needs an answer.")
                return
            
            user_id = message.from_user.id
            username = message.from_user.username or str(user_id)
            
            # ذخیره موقت need
            user_needs[user_id] = need
            
            # ساخت فاکتور با Crypto Pay API
            url = "https://pay.crypt.bot/api/createInvoice"
            headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
            payload = {
                "asset": "USDT",
                "amount": "1",  # ۱ دلار USDT
                "description": f"Release your burden: {need}",
                "payload": f"{user_id}:{need}",  # برای شناسایی در webhook
                "paid_btn_name": "callback",
                "paid_btn_url": "https://t.me/yourbotusername"  # لینک دلخواه بعد از پرداخت
            }
            
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                result = response.json()["result"]
                pay_url = result["bot_invoice_url"]  # لینک مناسب برای داخل تلگرام
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="💰 PAY $1 WITH CRYPTO", url=pay_url)
                ]])
                
                await message.answer(
                    f"VOID IS READY.\n\nYour burden: 「 {need.upper()} 」\n\nPay $1 to release it forever.",
                    reply_markup=keyboard
                )
            else:
                await message.answer("Payment error. Try again later.")
    except Exception as e:
        await message.answer("Something went wrong. Try again.")

# هندلر /start
@dp.message(Command("start"))
async def start(message: types.Message):
    btn = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⚫ ENTER THE VOID", web_app=WebAppInfo(url=f"{BASE_URL}/static/index.html"))
    ]])
    await message.answer("Welcome to The Void.\nLeave your burdens behind.", reply_markup=btn)

# وب‌هوک پرداخت موفق Crypto Pay
@app.post("/crypto_callback")
async def crypto_callback(request: Request):
    try:
        data = await request.json()
        if data.get("update_type") == "invoice_paid":
            invoice = data["payload"]  # اینجا payload که خودمون فرستادیم
            custom_payload = invoice.get("payload", "")
            if ":" in custom_payload:
                user_id_str, need = custom_payload.split(":", 1)
                user_id = int(user_id_str)
                
                # تولید گواهی
                path = create_certificate(str(user_id), need)
                
                # ارسال گواهی
                await bot.send_document(
                    chat_id=user_id,
                    document=FSInputFile(path),
                    caption="YOU ARE NOW FREE.\nThe Void has accepted your burden forever."
                )
                
                # پاک کردن فایل موقت (اختیاری)
                os.remove(path)
                
                # پاک کردن need ذخیره‌شده
                user_needs.pop(user_id, None)
                
        return {"ok": True}
    except Exception:
        return {"ok": False}

# سرو استاتیک فایل‌ها
app.mount("/static", StaticFiles(directory="static"), name="static")