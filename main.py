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

from cert_gen import create_certificate

load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
CRYPTO_TOKEN = os.getenv("CRYPTO_PAY_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
app = FastAPI()

logging.basicConfig(level=logging.INFO)

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔱 ASCEND TO THE VOID", web_app=WebAppInfo(url=f"{WEBHOOK_URL}/static/index.html"))
    ]])
    await message.answer(
        "<b>Welcome to the Void.</b>\nYour burdens are temporary. Digital eternity is forever.",
        reply_markup=markup, parse_mode="HTML"
    )

@dp.message(lambda message: message.web_app_data is not None)
async def handle_webapp_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        burden = data.get("need", "Unknown")
        
        headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
        payload = {
            "asset": "USDT", "amount": "1.00",
            "description": f"NFT Minting: {burden}",
            "payload": f"{message.from_user.id}:{burden}",
            "paid_btn_name": "openBot",
            "paid_btn_url": f"https://t.me/{(await bot.get_me()).username}"
        }
        
        res = requests.post("https://pay.cryptotextnet.me/api/createInvoice", headers=headers, json=payload).json()
        if res.get('ok'):
            pay_url = res['result']['pay_url']
            btn = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="💳 MINT NFT PROOF ($1)", url=pay_url)
            ]])
            await message.answer(f"Ritual for <b>{burden}</b> recorded. Mint your eternal proof now:", reply_markup=btn, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Error: {e}")

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
    data = await request.json()
    status = data.get('update_type') or data.get('status')
    if status in ['invoice_paid', 'paid']:
        payload = data.get('payload') or data.get('request_data', {}).get('payload')
        if payload:
            user_id, burden = payload.split(":")
            bg_tasks.add_task(send_final_reward, user_id, burden)
    return {"ok": True}

async def send_final_reward(user_id, burden):
    try:
        # ۱. تولید گواهی با متادیتای NFT
        cert_path = create_certificate(str(user_id), burden)
        
        # ۲. ارسال به کاربر
        if os.path.exists(cert_path):
            caption = (
                f"🔱 **NFT MINTED SUCCESSFULLY**\n\n"
                f"**Asset:** {burden}\n"
                f"**Status:** Registered in the Void\n\n"
                f"This certificate is your unique proof of sacrifice."
            )
            await bot.send_document(chat_id=user_id, document=FSInputFile(cert_path), caption=caption, parse_mode="Markdown")
            os.remove(cert_path)

        # ۳. ارسال وویس نجوا
        voice_file = "_Everything you were.ogg"
        if os.path.exists(voice_file):
            await bot.send_voice(chat_id=user_id, voice=FSInputFile(voice_file))

    except Exception as e:
        logging.error(f"Final error: {e}")

app.mount("/static", StaticFiles(directory="static"), name="static")
