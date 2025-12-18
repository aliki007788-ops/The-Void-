import os, json, base64, logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, Update, FSInputFile, LabeledPrice
from aiogram.filters import Command
from cert_gen import create_certificate
from dotenv import load_dotenv

# پیکربندی لاگ برای عیب‌یابی سریع در سرور
logging.basicConfig(level=logging.INFO)
load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
app = FastAPI()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """نقطه ورود کاربر و باز کردن مینی‌آپ"""
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🔱 ASCEND TO THE VOID", 
            web_app=WebAppInfo(url=f"{os.getenv('WEBHOOK_URL')}/static/index.html")
        )
    ]])
    await message.answer(
        "<b>THE VOID IS CALLING.</b>\nWill you sacrifice your burden for eternal peace?",
        reply_markup=kb,
        parse_mode="HTML"
    )

@app.get("/create_stars_invoice")
async def create_inv(d: str):
    """دریافت درخواست فاکتور از فرانت‌اِند"""
    try:
        # رمزگشایی Payload ارسالی از JS
        decoded = json.loads(base64.b64decode(d).decode('utf-8'))
        uid = decoded.get('u')
        burden = decoded.get('b')
        
        if not uid or not burden:
            return {"error": "Incomplete data"}

        # ایجاد لینک فاکتور Stars (قیمت: 50 ستاره)
        prices = [LabeledPrice(label="Ascension Ritual", amount=50)]
        link = await bot.create_invoice_link(
            title="THE VOID | PRESTIGE",
            description=f"Personalized NFT for: {burden}",
            payload=f"{uid}:{burden}",
            currency="XTR", 
            prices=prices
        )
        return {"url": link}
    except Exception as e:
        logging.error(f"Invoice Error: {e}")
        return {"error": "Cosmic interference"}

@dp.pre_checkout_query()
async def pre_checkout_handler(query: types.PreCheckoutQuery):
    """تأیید نهایی قبل از کسر وجه (اجباری تلگرام)"""
    await query.answer(ok=True)

@dp.message(F.successful_payment)
async def on_payment_success(message: types.Message):
    """اجرای عملیات پس از پرداخت موفق ستاره‌ها"""
    try:
        payload = message.successful_payment.invoice_payload
        uid_str, burden = payload.split(":")
        chat_id = int(uid_str)
        
        # ۱. تولید فایل تصویری گواهی
        nft_path = create_certificate(chat_id, burden)
        
        # ۲. ارسال مدرک دیجیتال به کاربر
        await bot.send_document(
            chat_id=chat_id, 
            document=FSInputFile(nft_path), 
            caption=f"🔱 <b>ASCENSION COMPLETE</b>\nYour burden <i>{burden}</i> is now stardust.\n\nAsset ID: #VOID-{chat_id}",
            parse_mode="HTML"
        )
        
        # ۳. ارسال فایل صوتی اتمسفریک (در صورت وجود)
        voice_path = "_Everything you were.ogg"
        if os.path.exists(voice_path):
            await bot.send_voice(chat_id=chat_id, voice=FSInputFile(voice_path))
        
        # پاکسازی خودکار فایل موقت
        if os.path.exists(nft_path):
            os.remove(nft_path)
            
    except Exception as e:
        logging.error(f"Post-Payment Error: {e}")

@app.post("/webhook")
async def handle_webhook(request: Request):
    """هندلر وب‌هوک تلگرام"""
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

# سرو فایل‌های استاتیک (HTML/JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(f"{os.getenv('WEBHOOK_URL')}/webhook")
