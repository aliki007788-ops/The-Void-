import os
import json
import requests
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    WebAppInfo,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    FSInputFile,
)
from aiogram import types

from cert_gen import create_certificate


# ================== ENV ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CRYPTO_TOKEN = os.getenv("CRYPTO_PAY_TOKEN")
BASE_URL = os.getenv("WEBHOOK_URL")  # e.g. https://your-app.onrender.com

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()


# ================== STARTUP ==================
@app.on_event("startup")
async def on_startup():
    webhook_url = f"{BASE_URL}/webhook"
    await bot.set_webhook(webhook_url)
    print(f"[VOID] Webhook set → {webhook_url}")


# ================== TELEGRAM WEBHOOK ==================
@app.post("/webhook")
async def telegram_webhook(request: Request):
    update = Update.model_validate(
        await request.json(),
        context={"bot": bot}
    )
    await dp.feed_update(bot=bot, update=update)
    return {"ok": True}


# ================== /start ==================
@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="⚫ ENTER THE VOID",
                web_app=WebAppInfo(
                    url=f"{BASE_URL}/static/index.html"
                )
            )
        ]]
    )

    await message.answer(
        "Welcome to The Void.\nLeave your burdens behind.",
        reply_markup=keyboard
    )


# ================== WEB APP DATA ==================
@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)

        if data.get("action") != "create_invoice":
            return

        need = data.get("need", "").strip()
        if not need:
            await message.answer("⚠️ The Void needs an answer.")
            return

        user_id = message.from_user.id

        url = "https://pay.cryptobot.io/api/createInvoice"
        headers = {
            "Crypto-Pay-API-Token": CRYPTO_TOKEN
        }

        payload = {
            "asset": "USDT",
            "amount": "1",
            "description": f"Release your burden: {need}",
            "payload": f"{user_id}:{need}",
            "paid_btn_name": "viewInvoice",
            "paid_btn_url": f"https://t.me/{(await bot.get_me()).username}",
        }

        response = requests.post(url, headers=headers, json=payload)
        result = response.json()

        if response.status_code == 200 and result.get("ok"):
            invoice = result["result"]
            pay_url = invoice["bot_invoice_url"]

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        text="💰 SEAL IT IN THE VOID — $1",
                        url=pay_url
                    )
                ]]
            )

            await message.answer(
                "🕳 VOID ACCEPTED.\n\n"
                f"Burden erased: 「 {need.upper()} 」\n\n"
                "Complete the ritual to receive your certificate.",
                reply_markup=keyboard
            )
        else:
            await message.answer("❌ Payment system error. Try again later.")

    except Exception as e:
        print(f"[VOID ERROR] {e}")
        await message.answer("❌ An error occurred. Try again.")


# ================== CRYPTO PAY CALLBACK ==================
@app.post("/crypto_callback")
async def crypto_callback(request: Request):
    try:
        data = await request.json()

        if data.get("update_type") != "invoice_paid":
            return {"ok": True}

        invoice = data.get("payload", {})
        payload = invoice.get("payload", "")

        if ":" not in payload:
            return {"ok": True}

        user_id_str, need = payload.split(":", 1)
        user_id = int(user_id_str)

        path = create_certificate(user_id_str, need)

        await bot.send_document(
            chat_id=user_id,
            document=FSInputFile(path),
            caption=(
                "YOU ARE NOW FREE.\n\n"
                "The Void has accepted your burden forever.\n"
                "Your official attestation is attached."
            )
        )

        if os.path.exists(path):
            os.remove(path)

        return {"ok": True}

    except Exception as e:
        print(f"[CRYPTO ERROR] {e}")
        return {"ok": False}


# ================== STATIC FILES ==================
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)
