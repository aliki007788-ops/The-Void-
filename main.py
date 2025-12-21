import os, json
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import LabeledPrice, FSInputFile
from cert_gen import create_certificate

app = FastAPI()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# قیمت‌ها بر اساس ستاره تلگرام
PRICES = {
    "vagabond": 0,
    "divine": 99,
    "celestial": 299,
    "legendary": 499,
    "luck": 30
}

@app.post("/create_stars_invoice")
async def create_invoice(request: Request):
    data = await request.json()
    uid, rank, burden = str(data['u']), data['rank'], data['b']
    price = PRICES.get(rank, 0)

    if price == 0:
        path = create_certificate(uid, burden, None, 'vagabond')
        await bot.send_document(uid, FSInputFile(path), caption=f"Void Identity: {burden}")
        return {"free": True}

    # ایجاد فاکتور پرداخت ستاره
    link = await bot.create_invoice_link(
        title=f"ASCENSION: {rank.upper()}",
        description=f"AI-Generated {rank} rank NFT Certificate.",
        payload=f"{uid}:{burden}:{rank}:{data.get('p', 'none')[:50]}",
        currency="XTR",
        prices=[LabeledPrice(label="Stars", amount=price)]
    )
    return {"url": link}

# بخش ۱۵: تالار افتخارات و مزایده
@app.post("/list_for_auction")
async def list_auction(request: Request):
    data = await request.json()
    # در اینجا تصویر به دیتابیس مزایده اضافه می‌شود
    return {"status": "Listed on Auction House"}

@app.get("/get_hall_of_fame")
async def get_hall():
    # بازگرداندن ۱۰ تصویر آخر ساخته شده
    files = os.listdir("static/outputs")[-10:]
    return {"images": [f"/static/outputs/{f}" for f in files]}

app.mount("/static", StaticFiles(directory="static"))
