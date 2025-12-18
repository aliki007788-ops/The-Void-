import os
import logging
import requests
from fastapi import FastAPI, Request, BackgroundTasks
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, Update, FSInputFile
from dotenv import load_dotenv

# وارد کردن تابع تولید گواهی از فایل cert_gen.py
from cert_gen import create_certificate

# تنظیمات اولیه
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
CRYPTO_TOKEN = os.getenv("CRYPTO_PAY_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL") # مثال: https://your-app.render.com

# راه‌اندازی ربات و اپلیکیشن
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
app = FastAPI()

logging.basicConfig(level=logging.INFO)

# --- بخش مدیریت تلگرام ---

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    """خوش‌آمدگویی و باز کردن مینی‌اپ لوکس"""
    markup = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🔱 ENTER THE VOID", 
            web_app=WebAppInfo(url=f"{WEBHOOK_URL}/static/index.html")
        )
    ]])
    
    await message.answer(
        "<b>Welcome to THE VOID.</b>\n\n"
        "Here, your burdens are transmuted into nothingness. "
        "Proceed to the ritual.",
        reply_markup=markup,
        parse_mode="HTML"
    )

@dp.message(lambda message: message.web_app_data is not None)
async def web_app_data_handler(message: types.Message):
    """دریافت داده از مینی‌اپ و ایجاد فاکتور پرداخت"""
    import json
    data = json.loads(message.web_app_data.data)
    burden_text = data.get("need", "Unknown Burden")
    
    # ایجاد فاکتور در Crypto Pay (۱ دلار تتر یا معادل آن)
    headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
    payload = {
        "asset": "USDT",
        "amount": "1.00",
        "description": f"The Void: Erasing {burden_text}",
        "payload": f"{message.from_user.id}:{burden_text}", # ذخیره اطلاعات در فاکتور
        "paid_btn_name": "viewItem",
        "paid_btn_url": "https://t.me/YourBotUsername"
    }
    
    try:
        response = requests.post(
            "https://pay.cryptotextnet.me/api/createInvoice", # آدرس مستقیم CryptoBot API
            headers=headers, 
            json=payload
        )
        result = response.json()
        
        if result['ok']:
            pay_url = result['result']['pay_url']
            btn = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="💳 PAY $1 TO RELEASE", url=pay_url)
            ]])
            await message.answer(
                f"The ritual for <b>'{burden_text}'</b> is ready.\n"
                "Once the payment is confirmed, your certificate of rebirth will be issued.",
                reply_markup=btn,
                parse_mode="HTML"
            )
    except Exception as e:
        await message.answer("The Void is momentarily unstable. Try again.")

# --- بخش وب‌هوک و پرداخت (Automated Engine) ---

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """پردازش آپدیت‌های تلگرام"""
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.post("/pay_callback")
async def crypto_pay_callback(request: Request, background_tasks: BackgroundTasks):
    """وب‌هوک تایید پرداخت: قلب تپنده سیستم"""
    data = await request.json()
    
    # بررسی وضعیت پرداخت (توسط Crypto Pay ارسال می‌شود)
    if data.get('status') == 'paid' or data.get('update_type') == 'invoice_paid':
        # استخراج اطلاعات از Payload
        payload_data = data['payload'] if 'payload' in data else data['request_data']['payload']
        user_id, burden = payload_data.split(":")
        
        # اجرای عملیات سنگین (تولید تصویر) در پس‌زمینه برای جلوگیری از Timeout
        background_tasks.add_task(send_final_certificate, user_id, burden)
        
    return {"ok": True}

async def send_final_certificate(user_id, burden):
    """تولید و ارسال گواهی به صورت کاملاً خودکار"""
    try:
        # ۱. تولید گواهی با استفاده از موتور هنری cert_gen
        file_path = create_certificate(str(user_id), burden) [cite: 100]
        
        # ۲. ارسال پیام نهایی با استایل سینمایی
        await bot.send_document(
            chat_id=user_id,
            document=FSInputFile(file_path),
            caption=(
                "<b>THE RITUAL IS COMPLETE.</b>\n\n"
                f"The burden of <i>'{burden}'</i> has been atomized.\n"
                "You are now free. Carry this attestation as a symbol of your rebirth."
            ),
            parse_mode="HTML"
        )
        
        # ۳. حذف فایل برای صرفه‌جویی در فضای سرور
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        logging.error(f"Error in final delivery: {e}")

# سرو کردن فایل‌های استاتیک مینی‌اپ
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")
