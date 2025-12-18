import os, json, requests, base64, logging
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, Update, FSInputFile
from aiogram.filters import Command
from cert_gen import create_certificate
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
app = FastAPI()

@dp.message(Command("start"))
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔱 ENTER THE VOID", web_app=WebAppInfo(url=f"{os.getenv('WEBHOOK_URL')}/static/index.html"))
    ]])
    await message.answer("<b>THE VOID AWAITS.</b>", reply_markup=kb, parse_mode="HTML")

@app.get("/pay")
async def process_payment(d: str):
    """جایی که دکمه دوم جادو می‌کند"""
    try:
        decoded = json.loads(base64.b64decode(d))
        user_id = decoded['u']
        burden = decoded['b']
        
        headers = {"Crypto-Pay-API-Token": os.getenv("CRYPTO_PAY_TOKEN")}
        payload = {
            "asset": "USDT", "amount": "1.00",
            "description": f"NFT Certificate: {burden}",
            "payload": f"{user_id}:{burden}"
        }
        res = requests.post("https://pay.cryptotextnet.me/api/createInvoice", headers=headers, json=payload).json()
        
        if res.get('ok'):
            return RedirectResponse(url=res['result']['pay_url'])
        return {"error": "Invoice creation failed"}
    except Exception as e:
        logging.error(f"Payment Error: {e}")
        return {"error": str(e)}

@app.post("/webhook")
async def webhook(request: Request):
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.post("/pay_callback")
async def payment_callback(request: Request, bg: BackgroundTasks):
    data = await request.json()
    if data.get('update_type') == 'invoice_paid':
        uid, bur = data['payload'].split(":")
        bg.add_task(send_nft_final, uid, bur)
    return {"ok": True}

async def send_nft_final(uid, bur):
    path = create_certificate(uid, bur)
    await bot.send_document(uid, FSInputFile(path), caption=f"🔱 <b>NFT MINTED</b>\nYour burden '{bur}' is now stardust.")
    if os.path.exists("_Everything you were.ogg"):
        await bot.send_voice(uid, FSInputFile("_Everything you were.ogg"))
    os.remove(path)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(f"{os.getenv('WEBHOOK_URL')}/webhook")
