import os, json, requests, base64
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, Update, FSInputFile
from aiogram.filters import Command
from cert_gen import create_certificate
from dotenv import load_dotenv

load_dotenv()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
app = FastAPI()

@dp.message(Command("start"))
async def start(message: types.Message):
    # اطمینان از HTTPS بودن URL
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔱 ASCEND TO THE VOID", web_app=WebAppInfo(url=f"{os.getenv('WEBHOOK_URL')}/static/index.html"))
    ]])
    await message.answer("<b>THE VOID IS READY.</b>", reply_markup=kb, parse_mode="HTML")

@app.get("/pay_now")
async def pay_now(d: str):
    """هدایت مستقیم کاربر به درگاه جهت جلوگیری از فریز شدن در تلگرام وب"""
    try:
        decoded = json.loads(base64.b64decode(d).decode('utf-8'))
        uid, burden = decoded['u'], decoded['b']
        
        headers = {"Crypto-Pay-API-Token": os.getenv("CRYPTO_PAY_TOKEN")}
        payload = {
            "asset": "USDT", "amount": "1.00", # اینجا می‌توانید به TON تغییر دهید
            "description": f"VOID NFT: {burden}",
            "payload": f"{uid}:{burden}"
        }
        res = requests.post("https://pay.cryptotextnet.me/api/createInvoice", headers=headers, json=payload).json()
        
        if res.get('ok'):
            return RedirectResponse(url=res['result']['pay_url'])
        return {"error": "Payment gateway unreachable"}
    except Exception as e:
        return {"error": f"Internal Connection Error: {str(e)}"}

@app.post("/webhook")
async def webhook(request: Request):
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.post("/pay_callback")
async def callback(request: Request, bg: BackgroundTasks):
    data = await request.json()
    if data.get('update_type') == 'invoice_paid':
        uid, bur = data['payload'].split(":")
        bg.add_task(send_nft_result, uid, bur)
    return {"ok": True}

async def send_nft_result(uid, bur):
    path = create_certificate(uid, bur)
    await bot.send_document(uid, FSInputFile(path), caption=f"🔱 <b>SUCCESSFUL ASCENSION</b>\nYour burden '{bur}' is immortalized.")
    if os.path.exists("_Everything you were.ogg"):
        await bot.send_voice(uid, FSInputFile("_Everything you were.ogg"))
    os.remove(path)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup():
    await bot.set_webhook(f"{os.getenv('WEBHOOK_URL')}/webhook")
