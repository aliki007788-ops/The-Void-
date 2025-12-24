import os
import json
import base64
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Update, FSInputFile, LabeledPrice
from cert_gen import create_certificate
from dotenv import load_dotenv

load_dotenv()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
app = FastAPI()

# دیتابیس و تنظیمات اولیه [cite: 523-528]
DB_FILE = "void_db.json"
DB = json.load(open(DB_FILE)) if os.path.exists(DB_FILE) else {"users": {}}

@app.post("/create_stars_invoice")
async def create_invoice(request: Request):
    data = await request.json()
    uid, plan, burden = data['u'], data['type'], data.get('b', 'Soul')
    
    # منطق رایگان [cite: 639-655]
    if plan == 'free':
        path, style = create_certificate(uid, burden, "Eternal")
        await bot.send_document(uid, FSInputFile(path), caption=f"🔱 {burden.upper()} ASCENDED")
        return {"free": True}

    # منطق پرداخت Stars [cite: 693-700]
    prices = {"divine": 150, "celestial": 299, "legendary": 499, "kings-luck": 199}
    link = await bot.create_invoice_link(
        title=f"VOID {plan.upper()}",
        description="Eternal Ascension",
        payload=f"{uid}:{burden}:{plan}",
        currency="XTR",
        prices=[LabeledPrice("Stars", prices[plan])]
    )
    return {"url": link}

@dp.message(F.successful_payment)
async def on_payment(message: types.Message):
    uid, burden, plan = message.successful_payment.invoice_payload.split(":")
    level = "Legendary" if plan == "legendary" else "Divine"
    path, style = create_certificate(uid, burden, level)
    await bot.send_document(uid, FSInputFile(path), caption="Payment Received. You have Ascended.")

app.mount("/static", StaticFiles(directory="static")) # [cite: 720]

@app.post("/webhook")
async def webhook(request: Request):
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}
