import os, json, requests, logging
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, Update, FSInputFile
from aiogram.filters import Command
from cert_gen import create_certificate
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
CRYPTO_TOKEN = os.getenv("CRYPTO_PAY_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
app = FastAPI()

@dp.message(Command("start"))
async def start(message: types.Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔱 ASCEND TO THE VOID", web_app=WebAppInfo(url=f"{WEBHOOK_URL}/static/index.html"))
    ]])
    await message.answer("<b>THE VOID IS READY.</b>", reply_markup=markup, parse_mode="HTML")

@dp.message(lambda message: message.web_app_data is not None)
async def handle_webapp_data(message: types.Message):
    """بخش حیاتی: دریافت داده و صدور آنی فاکتور"""
    try:
        data = json.loads(message.web_app_data.data)
        burden = data.get("need", "Something")
        
        headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
        payload = {
            "asset": "USDT", "amount": "1.00",
            "description": f"NFT Certificate for {burden}",
            "payload": f"{message.from_user.id}:{burden}"
        }
        
        # فراخوانی API کریپتو بات
        response = requests.post("https://pay.cryptotextnet.me/api/createInvoice", headers=headers, json=payload).json()
        
        if response.get('ok'):
            pay_url = response['result']['pay_url']
            btn = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="💳 PAY & MINT NFT", url=pay_url)
            ]])
            await message.answer(f"Transaction for <b>{burden}</b> initialized.\nFinalize below:", reply_markup=btn, parse_mode="HTML")
        else:
            await message.answer("Connection to CryptoPay failed. Please retry.")
            
    except Exception as e:
        logging.error(f"Error in handle_webapp_data: {e}")

@app.post("/webhook")
async def telegram_webhook(request: Request):
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.post("/pay_callback")
async def payment_webhook(request: Request, bg_tasks: BackgroundTasks):
    data = await request.json()
    if data.get('update_type') == 'invoice_paid':
        payload = data.get('payload', '')
        if ":" in payload:
            user_id, burden = payload.split(":")
            bg_tasks.add_task(send_nft_reward, user_id, burden)
    return {"ok": True}

async def send_nft_reward(user_id, burden):
    cert_path = create_certificate(str(user_id), burden)
    await bot.send_document(chat_id=user_id, document=FSInputFile(cert_path), caption=f"🔱 NFT Minted: {burden}")
    if os.path.exists("_Everything you were.ogg"):
        await bot.send_voice(chat_id=user_id, voice=FSInputFile("_Everything you were.ogg"))
    os.remove(cert_path)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
