import os
import base64
import tempfile
import requests
from io import BytesIO
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import LabeledPrice, FSInputFile
from cert_gen import create_certificate

app = FastAPI()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# Hugging Face API (Stable Diffusion XL img2img)
HF_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
HF_HEADERS = {"Authorization": f"Bearer {os.getenv('HF_TOKEN')}"}

# قیمت پلن‌ها
PRICES = {
    'vagabond': 0,      # رایگان - سطح 1
    'divine': 99,       # سطح 2
    'celestial': 299,   # سطح 3
    'legendary': 499    # سطح 4
}

@app.post("/create_stars_invoice")
async def create_invoice(request: Request):
    data = await request.json()
    uid = data['u']
    rank = data.get('rank', 'vagabond')
    price = PRICES.get(rank, 0)
    
    photo_path = "none"
    if data.get('p'):
        img_data = base64.b64decode(data['p'].split(',')[1])
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(img_data)
            photo_path = tmp.name
    
    if price == 0:
        path = create_certificate(uid, data['b'], None if photo_path == "none" else photo_path, rank)
        await bot.send_document(uid, FSInputFile(path), caption="Your Vagabond Soul is recorded in the Eternal Void.")
        if photo_path != "none": os.remove(photo_path)
        return {"free": True}
    
    invoice_link = await bot.create_invoice_link(
        title=f"ASCENSION TO {rank.upper()}",
        description=f"Sacrifice for the {rank.upper()} eternal certificate.",
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
    
    await bot.send_document(uid, FSInputFile(path), caption="The Void has accepted your eternal offering.")
    if actual_photo and actual_photo != "none": os.remove(actual_photo)

app.mount("/static", StaticFiles(directory="static"))
