import os, json, requests, logging
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, Update, FSInputFile
from aiogram.filters import Command
from cert_gen import create_certificate
from dotenv import load_dotenv

load_dotenv()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
app = FastAPI()

@dp.message(Command("start"))
async def start(message: types.Message):
    # دکمه ورود به مینی اپ
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔱 ASCEND TO THE VOID", web_app=WebAppInfo(url=f"{os.getenv('WEBHOOK_URL')}/static/index.html"))
    ]])
    await message.answer("<b>THE VOID IS WAITING.</b>", reply_markup=kb, parse_mode="HTML")

@dp.message(lambda m: m.web_app_data is not None)
async def handle_webapp_data(message: types.Message):
    """دریافت داده از مینی اپ و صدور فاکتور"""
    try:
        data = json.loads(message.web_app_data.data)
        burden = data.get("need", "Sacrifice")
        
        # ساخت فاکتور در CryptoPay
        headers = {"Crypto-Pay-API-Token": os.getenv("CRYPTO_PAY_TOKEN")}
        payload = {
            "asset": "USDT", "amount": "1.00",
            "description": f"NFT Certificate: {burden}",
            "payload": f"{message.from_user.id}:{burden}"
        }
        res = requests.post("https://pay.cryptotextnet.me/api/createInvoice", headers=headers, json=payload).json()
        
        if res.get('ok'):
            pay_url = res['result']['pay_url']
            kb = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="💳 MINT NFT ($1.00)", url=pay_url)
            ]])
            await message.answer(f"Ritual for <b>{burden}</b> is ready.\nProceed to mint your eternal proof on the blockchain:", reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        logging.error(e)

@app.post("/webhook")
async def webhook_update(request: Request):
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.post("/pay_callback")
async def payment_success(request: Request, bg: BackgroundTasks):
    data = await request.json()
    if data.get('update_type') == 'invoice_paid':
        uid, bur = data['payload'].split(":")
        bg.add_task(finalize_nft, uid, bur)
    return {"ok": True}

async def finalize_nft(uid, bur):
    # تولید گواهی NFT
    path = create_certificate(uid, bur)
    await bot.send_document(uid, FSInputFile(path), caption=f"🔱 **NFT MINTED**\nYour burden '{bur}' is now stardust.")
    if os.path.exists("_Everything you were.ogg"):
        await bot.send_voice(uid, FSInputFile("_Everything you were.ogg"))
    os.remove(path)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(f"{os.getenv('WEBHOOK_URL')}/webhook")
