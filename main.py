import os
import json
import requests
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, Update, FSInputFile
from aiogram import types
from cert_gen import create_certificate
from fastapi.staticfiles import StaticFiles

# متغیرهای محیطی
TOKEN = os.getenv("BOT_TOKEN")
CRYPTO_TOKEN = os.getenv("CRYPTO_PAY_TOKEN")
BASE_URL = os.getenv("WEBHOOK_URL")  # مثلاً https://the-void-95yc.onrender.com

bot = Bot(token=TOKEN)
dp = Dispatcher()
app = FastAPI()

# راه‌اندازی وب‌هوک موقع استارتاپ
@app.on_event("startup")
async def on_startup():
    webhook_url = f"{BASE_URL}/webhook"
    await bot.set_webhook(url=webhook_url)
    print(f"Webhook set to {webhook_url}")

# وب‌هوک تلگرام
@app.post("/webhook")
async def telegram_webhook(request: Request):
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot=bot, update=update)

# هندلر /start
@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⚫ ENTER THE VOID", web_app=WebAppInfo(url=f"{BASE_URL}/static/index.html"))
    ]])
    await message.answer(
        "Welcome to The Void.\nLeave your burdens behind.",
        reply_markup=keyboard
    )

# هندلر داده از مینی‌اپ (بعد از انیمیشن ذرات)
@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        if data.get("action") == "create_invoice":
            need = data["need"].strip()
            if not need:
                await message.answer("⚠️ The Void needs an answer.")
                return

            user_id = message.from_user.id

            # ساخت فاکتور پرداخت
            url = "https://pay.cryptobot.io/api/createInvoice"
            headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
            payload = {
                "asset": "USDT",
                "amount": "1",
                "description": f"Release your burden: {need}",
                "payload": f"{user_id}:{need}",
                "paid_btn_name": "viewInvoice",
                "paid_btn_url": f"https://t.me/{(await bot.get_me()).username}"
            }

            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200 and response.json().get("ok"):
                result = response.json()["result"]
                pay_url = result["bot_invoice_url"]

                keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="💰 PAY $1 & RELEASE FOREVER", url=pay_url)
                ]])

                await message.answer(
                    f"VOID ACCEPTED.\n\n"
                    f"Your burden: 「 {need.upper()} 」\n\n"
                    f"Pay $1 to receive your official luxury certificate.",
                    reply_markup=keyboard
                )
            else:
                await message.answer("❌ Payment system error. Try again later.")
    except Exception as e:
        print(f"Error in webapp handler: {e}")
        await message.answer("❌ An error occurred. Try again.")

# وب‌هوک پرداخت موفق Crypto Pay
@app.post("/crypto_callback")
async def crypto_callback(request: Request):
    try:
        data = await request.json()
        if data.get("update_type") == "invoice_paid":
            invoice = data["payload"]
            custom_payload = invoice.get("payload", "")
            if ":" in custom_payload:
                user_id_str, need = custom_payload.split(":", 1)
                user_id = int(user_id_str)

                # تولید و ارسال گواهی
                path = create_certificate(str(user_id), need)
                await bot.send_document(
                    chat_id=user_id,
                    document=FSInputFile(path),
                    caption="YOU ARE NOW FREE.\n\nThe Void has accepted your burden forever.\nYour official attestation is attached."
                )
                # پاک کردن فایل موقت
                if os.path.exists(path):
                    os.remove(path)

        return {"ok": True}
    except Exception as e:
        print(f"Crypto callback error: {e}")
        return {"ok": False}

# سرو فایل‌های استاتیک (مینی‌اپ)
app.mount("/static", StaticFiles(directory="static"), name="static")
