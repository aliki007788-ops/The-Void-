import os, json, base64, tempfile
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, Update, FSInputFile, LabeledPrice
from cert_gen import create_certificate
from dotenv import load_dotenv

load_dotenv()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
app = FastAPI()

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
PRICE_BASIC, PRICE_PREMIUM = 70, 120
VIP_CODES = {"VOID-ADMIN", "FREE-NFT"} # نمونه کدهای VIP

async def send_nft(uid: int, burden: str, photo_path: str = None):
    nft = create_certificate(uid, burden, photo_path)
    await bot.send_document(uid, FSInputFile(nft), caption="🔱 <b>ASCENSION COMPLETE</b>", parse_mode="HTML")
    if photo_path and os.path.exists(photo_path): os.remove(photo_path)
    if os.path.exists(nft): os.remove(nft)

@app.post("/create_stars_invoice")
async def invoice(request: Request):
    data = await request.json()
    uid = data.get('u')
    burden = data.get('b', '').upper().strip()

    if burden in VIP_CODES:
        await send_nft(uid, burden)
        return {"free": True}

    premium = bool(data.get('p') or data.get('prof'))
    amount = PRICE_PREMIUM if premium else PRICE_BASIC
    
    temp_p = "none"
    if data.get('p'):
        img = base64.b64decode(data['p'].split(',')[1])
        t = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        t.write(img); t.close()
        temp_p = t.name

    payload = f"{uid}:{burden}:{temp_p}:{1 if data.get('prof') else 0}"
    link = await bot.create_invoice_link(
        title="VOID ASCENSION",
        description="Divine Record" if premium else "Eternal Record",
        payload=payload,
        currency="XTR",
        prices=[LabeledPrice(label="Fee", amount=amount)]
    )
    return {"url": link}

@dp.pre_checkout_query()
async def pre_checkout(q: types.PreCheckoutQuery):
    await q.answer(ok=True)

@dp.message(F.successful_payment)
async def paid(m: types.Message):
    p = m.successful_payment.invoice_payload.split(":")
    await send_nft(int(p[0]), p[1], p[2] if p[2] != "none" else None)

app.mount("/static", StaticFiles(directory="static"))

@app.post("/webhook")
async def webhook(r: Request):
    update = Update.model_validate(await r.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.on_event("startup")
async def start():
    await bot.set_webhook(f"{os.getenv('WEBHOOK_URL')}/webhook")
