import os, json, base64
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, Update, FSInputFile, LabeledPrice
from aiogram.filters import Command
from cert_gen import create_certificate
from dotenv import load_dotenv

load_dotenv()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
app = FastAPI()

@dp.message(Command("start"))
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔱 ASCEND TO THE VOID", web_app=WebAppInfo(url=f"{os.getenv('WEBHOOK_URL')}/static/index.html"))
    ]])
    await message.answer("<b>THE VOID AWAITS.</b>", reply_markup=kb, parse_mode="HTML")

@app.get("/create_invoice")
async def create_inv(d: str):
    """ایجاد لینک فاکتور Stars برای پرداخت داخلی"""
    try:
        decoded = json.loads(base64.b64decode(d).decode('utf-8'))
        uid, burden = decoded['u'], decoded['b']
        
        # تعیین قیمت (مثلاً ۵۰ استارز)
        prices = [LabeledPrice(label="Ascension Proof", amount=50)]
        
        link = await bot.create_invoice_link(
            title="THE VOID | PRESTIGE",
            description=f"Immortalize: {burden}",
            payload=f"{uid}:{burden}",
            currency="XTR", # واحد پول Stars
            prices=prices
        )
        return {"invoice_url": link}
    except Exception as e:
        return {"error": str(e)}

@dp.pre_checkout_query()
async def pre_checkout(query: types.PreCheckoutQuery):
    """تأیید نهایی قبل از کسر وجه (اجباری تلگرام)"""
    await query.answer(ok=True)

@dp.message(F.successful_payment)
async def on_payment(message: types.Message):
    """هندل کردن پرداخت موفق و ارسال ان‌اف‌تی"""
    payload = message.successful_payment.invoice_payload
    uid, burden = payload.split(":")
    
    path = create_certificate(uid, burden)
    await bot.send_document(uid, FSInputFile(path), caption=f"🔱 <b>ASCENSION COMPLETE</b>\nBurden '{burden}' is now eternal.")
    if os.path.exists("_Everything you were.ogg"):
        await bot.send_voice(uid, FSInputFile("_Everything you were.ogg"))
    os.remove(path)

@app.post("/webhook")
async def webhook(request: Request):
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(f"{os.getenv('WEBHOOK_URL')}/webhook")
