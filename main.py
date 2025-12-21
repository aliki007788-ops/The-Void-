import os, json
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import LabeledPrice, FSInputFile
from cert_gen import create_certificate

app = FastAPI()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# دیتابیس ساده برای ذخیره رفرال‌ها و تعداد استفاده
DB_FILE = "database.json"
def get_db():
    if not os.path.exists(DB_FILE): return {"users": {}, "hall": []}
    return json.load(open(DB_FILE))

def save_db(db): json.dump(db, open(DB_FILE, 'w'))

@app.post("/create_stars_invoice")
async def create_invoice(request: Request):
    data = await request.json()
    uid, burden, rank = str(data['u']), data['b'], data.get('rank', 'free')
    
    if rank == 'free':
        db = get_db()
        user_data = db['users'].get(uid, {"mints": 0})
        if user_data['mints'] >= 3: return {"error": "Limit Reached"}
        
        path = create_certificate(uid, burden, None, 'free')
        user_data['mints'] += 1
        db['users'][uid] = user_data
        db['hall'].insert(0, path)
        save_db(db)
        await bot.send_document(uid, FSInputFile(path), caption="Your free soul certificate.")
        return {"free": True}

    # قیمت‌گذاری پلن‌ها
    price = 30 if data.get('type') == 'luck' else (120 if rank == 'rare' else 299)
    
    link = await bot.create_invoice_link(
        title=f"THE VOID: {rank.upper()}",
        description=f"AI-Generated img2img Soul Certificate",
        payload=f"{uid}:{burden}:{rank}:{data.get('p', 'none')[:100]}", # نمونه اولیه
        currency="XTR",
        prices=[LabeledPrice(label="Stars", amount=price)]
    )
    return {"url": link}

@dp.message(F.successful_payment)
async def success_pay(message: types.Message):
    # توجه: در اینجا عکس کامل باید از دیتابیس موقت بازیابی شود
    payload = message.successful_payment.invoice_payload.split(":")
    uid, burden, rank = payload[0], payload[1], payload[2]
    
    # تولید تصویر با هوش مصنوعی Stable Diffusion
    path = create_certificate(uid, burden, None, rank) # در نسخه نهایی عکس از کش خوانده شود
    await bot.send_document(uid, FSInputFile(path), caption="🔱 Ascension Successful.")

app.mount("/static", StaticFiles(directory="static"))
