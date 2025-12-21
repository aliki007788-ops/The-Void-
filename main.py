import os, base64, tempfile
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import LabeledPrice, FSInputFile
from cert_gen import create_certificate

app = FastAPI()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# قیمت پلن‌ها به ستاره تلگرام
PRICES = {
    'free': 0,
    'rare': 120,
    'legendary': 299,
    'luck': 30
}

@app.post("/create_stars_invoice")
async def create_invoice(request: Request):
    data = await request.json()
    uid = data['u']
    rank = data.get('rank', 'free')
    price = PRICES.get(rank, 0)
    
    # ذخیره تصویر موقت در صورت وجود
    photo_path = "none"
    if data.get('p'):
        img_data = base64.b64decode(data['p'].split(',')[1])
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(img_data)
            photo_path = tmp.name

    if price == 0:
        # هندل کردن پلن رایگان (محدودیت ۳ تصویر در دیتابیس باید چک شود)
        path = create_certificate(uid, data['b'], None, 'free')
        await bot.send_document(uid, FSInputFile(path), caption="Your Vagabond Soul is recorded.")
        return {"free": True}

    # ایجاد لینک پرداخت ستاره
    invoice_link = await bot.create_invoice_link(
        title=f"ASCENSION TO {rank.upper()}",
        description=f"Sacrifice for the {rank} rank certificate.",
        payload=f"{uid}:{data['b']}:{photo_path}:{rank}",
        currency="XTR",
        prices=[LabeledPrice(label="Stars", amount=price)]
    )
    return {"url": invoice_link}

@dp.message(F.successful_payment)
async def on_payment(message: types.Message):
    payload = message.successful_payment.invoice_payload.split(":")
    uid, burden, photo, rank = int(payload[0]), payload[1], payload[2], payload[3]
    
    actual_photo = None if photo == "none" else photo
    path = create_certificate(uid, burden, actual_photo, rank)
    
    await bot.send_document(uid, FSInputFile(path), caption="The Void has accepted your offering.")
    if actual_photo: os.remove(actual_photo)

app.mount("/static", StaticFiles(directory="static"))
