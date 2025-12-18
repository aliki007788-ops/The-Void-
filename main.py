import os, json, base64
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, Update, FSInputFile, LabeledPrice
from aiogram.filters import Command
from cert_gen import create_certificate  # وارد کردن تابع فایل اول
from dotenv import load_dotenv

load_dotenv()

# تنظیمات اصلی
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    """ارسال دکمه ورود به مینی‌اپ"""
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🔱 ASCEND TO THE VOID", 
            web_app=WebAppInfo(url=f"{WEBHOOK_URL}/static/index.html")
        )
    ]])
    await message.answer(
        "<b>WELCOME TO THE VOID.</b>\nYour journey to eternity begins here.",
        reply_markup=kb,
        parse_mode="HTML"
    )

@app.get("/create_stars_invoice")
async def create_invoice(d: str):
    """ساخت لینک پرداخت Stars که فرانت‌اِند آن را فراخوانی می‌کند"""
    try:
        # رمزگشایی دیتای ارسالی از مینی‌اپ
        decoded = json.loads(base64.b64decode(d).decode('utf-8'))
        uid, burden = decoded['u'], decoded['b']
        
        # قیمت به ستاره (مثلاً ۵۰ ستاره تلگرام)
        prices = [LabeledPrice(label="Eternity Fee", amount=50)]
        
        invoice_link = await bot.create_invoice_link(
            title="VOID ASCENSION NFT",
            description=f"Sacrifice Proof for: {burden}",
            payload=f"{uid}:{burden}", # ذخیره اطلاعات برای مرحله بعد از پرداخت
            currency="XTR", # واحد رسمی ستاره تلگرام
            prices=prices
        )
        return {"url": invoice_link}
    except Exception as e:
        return {"error": str(e)}

@dp.pre_checkout_query()
async def pre_checkout_handler(query: types.PreCheckoutQuery):
    """تأیید نهایی تراکنش توسط ربات (اجباری)"""
    await query.answer(ok=True)

@dp.message(F.successful_payment)
async def payment_success(message: types.Message):
    """این بخش وقتی اجرا می‌شود که پرداخت Stars با موفقیت انجام شد"""
    payload = message.successful_payment.invoice_payload
    user_id, burden = payload.split(":")
    
    # ۱. تولید تصویر NFT/گواهی
    nft_path = create_certificate(user_id, burden)
    
    # ۲. ارسال گواهی برای کاربر
    await bot.send_document(
        user_id, 
        FSInputFile(nft_path), 
        caption=f"🔱 <b>ASCENSION SUCCESSFUL</b>\nYour burden <i>{burden}</i> has been immortalized.\n\nAsset: VOID-NFT-2040",
        parse_mode="HTML"
    )
    
    # ۳. ارسال فایل صوتی (اگر در پوشه موجود باشد)
    voice_path = "_Everything you were.ogg"
    if os.path.exists(voice_path):
        await bot.send_voice(user_id, FSInputFile(voice_path))
    
    # پاکسازی فایل موقت
    if os.path.exists(nft_path):
        os.remove(nft_path)

@app.post("/webhook")
async def handle_webhook(request: Request):
    """دریافت آپدیت‌ها از تلگرام"""
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(f"{WEBHOOK_URL}/webhook")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
