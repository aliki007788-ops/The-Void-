import os, base64, tempfile, random
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, FSInputFile
from cert_gen import create_certificate
from dotenv import load_dotenv

load_dotenv()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
app = FastAPI()

# Database Mockup
user_referrals = {} # {uid: count}

@dp.message(F.text.startswith("/start"))
async def start(message: types.Message):
    uid = message.from_user.id
    ref_id = message.text.split("ref_")[1] if "ref_" in message.text else None
    if ref_id and int(ref_id) != uid:
        user_referrals[int(ref_id)] = user_referrals.get(int(ref_id), 0) + 1
    
    text = (
        "🌌 **WELCOME TO THE VOID**\n\n"
        "1. **Common**: Free forever.\n"
        "2. **Rare**: 120 ⭐ (Luxurious Glow)\n"
        "3. **Legendary**: 299 ⭐ (Divine 3D)\n\n"
        "🎁 **Referral**: Invite 3 friends for a 50% discount!\n"
        f"Your Link: `https://t.me/livevoidbot?start=ref_{uid}`"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔱 ENTER THE VOID", web_app=WebAppInfo(url=f"{os.getenv('WEBHOOK_URL')}/static/index.html"))
    ]])
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@app.post("/create_stars_invoice")
async def create_invoice(request: Request):
    data = await request.json()
    uid, burden, rank, price = data['u'], data['b'], data.get('rank', 'common'), data.get('price', 0)
    
    # King's Luck Logic
    if data.get('type') == 'luck':
        rank = 'legendary' if random.random() < 0.1 else 'common'
        price = 30
        title = "KING'S LUCK ATTEMPT"
    else:
        title = f"ASCENSION: {rank.upper()}"

    if price == 0:
        path, _ = create_certificate(uid, burden, None, 'common')
        await bot.send_document(uid, FSInputFile(path), caption="Your Free Soul Certificate.")
        return {"free": True}

    temp_path = "none"
    if data.get('p'):
        img_data = base64.b64decode(data['p'].split(',')[1])
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(img_data); temp_path = tmp.name

    link = await bot.create_invoice_link(
        title=title, description=f"Forging a {rank} certificate",
        payload=f"{uid}:{burden}:{temp_path}:{rank}",
        currency="XTR", prices=[LabeledPrice(label="Void Fee", amount=price)]
    )
    return {"url": link}

@dp.message(F.successful_payment)
async def payment_success(message: types.Message):
    payload = message.successful_payment.invoice_payload.split(":")
    uid, burden, photo, rank = int(payload[0]), payload[1], payload[2], payload[3]
    photo = None if photo == "none" else photo
    path, style_name = create_certificate(uid, burden, photo, rank)
    await bot.send_document(uid, FSInputFile(path), caption=f"🔱 **{style_name}**\nYour soul is eternal.")
    if photo: os.remove(photo)

app.mount("/static", StaticFiles(directory="static"))
@app.post("/webhook")
async def webhook(request: Request):
    update = types.Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}
