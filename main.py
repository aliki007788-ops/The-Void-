import os
import json
import random
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

DB_FILE = "void_db.json"
DB = json.load(open(DB_FILE)) if os.path.exists(DB_FILE) else {"users": {}}

def save_db():
    with open(DB_FILE, "w") as f: json.dump(DB, f)

@app.post("/create_stars_invoice")
async def create_invoice(request: Request):
    data = await request.json()
    uid, plan, burden = data['u'], data['type'], data.get('b', 'Unknown')
    
    # قیمت‌ها
    PRICES = {"divine": 150, "celestial": 299, "legendary": 499, "kings-luck": 199}

    if plan == 'free':
        # محدودیت رایگان
        user_str = str(uid)
        if user_str not in DB["users"]: DB["users"][user_str] = {"daily": 0}
        if DB["users"][user_str]["daily"] >= 3:
            return {"error": "Limit reached"}
        
        DB["users"][user_str]["daily"] += 1
        save_db()
        path, _ = create_certificate(uid, burden, "Eternal")
        await bot.send_document(uid, FSInputFile(path), caption=f"🔱 THE VOID ACCEPTS YOUR BURDEN: {burden}")
        return {"free": True}

    # پرداخت پولی
    link = await bot.create_invoice_link(
        title=f"ASCENSION: {plan.upper()}",
        description="Access the higher realms of THE VOID",
        payload=f"{uid}:{burden}:{plan}",
        currency="XTR",
        prices=[LabeledPrice("Stars", PRICES.get(plan, 150))]
    )
    return {"url": link}

@dp.message(F.successful_payment)
async def handle_payment(message: types.Message):
    payload = message.successful_payment.invoice_payload
    uid, burden, plan = payload.split(":")
    
    final_level = "Divine"
    if plan == "kings-luck":
        # منطق شانس پادشاه: ۵٪ لجندری، ۱۵٪ سلستیال، ۸۰٪ دیواین
        roll = random.random()
        if roll < 0.05: final_level = "Legendary"
        elif roll < 0.20: final_level = "Celestial"
        else: final_level = "Divine"
    else:
        final_level = plan.capitalize()

    path, style = create_certificate(int(uid), burden, final_level)
    await bot.send_document(uid, FSInputFile(path), 
        caption=f"🌌 **THE VOID HAS SPOKEN**\n\nYour rank: **{final_level}**\nBurden: *{burden}*")

app.mount("/static", StaticFiles(directory="static"))

@app.post("/webhook")
async def webhook(request: Request):
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}
