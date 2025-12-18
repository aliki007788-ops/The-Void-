import os, json, base64, logging, tempfile, requests
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, Update, FSInputFile, LabeledPrice
from cert_gen import create_certificate
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
app = FastAPI()

@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔱 ENTER THE VOID", web_app=WebAppInfo(url=f"{os.getenv('WEBHOOK_URL')}/static/index.html"))
    ]])
    await message.answer("<b>THE VOID AWAITS.</b>\nSacrifice your burden for eternal peace.", reply_markup=kb, parse_mode="HTML")

@app.get("/create_stars_invoice")
async def create_inv(d: str):
    try:
        data = json.loads(base64.b64decode(d).decode('utf-8'))
        temp_path = "none"
        if data.get('p'):
            img_data = base64.b64decode(data['p'].split(",")[1])
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            tmp.write(img_data)
            tmp.close()
            temp_path = tmp.name

        payload = f"{data['u']}:{data['b']}:{temp_path}:{1 if data.get('prof') else 0}"

        link = await bot.create_invoice_link(
            title="VOID NFT PRESTIGE",
            description=f"Sacrifice: {data['b']}",
            payload=payload,
            currency="XTR",
            prices=[LabeledPrice(label="Eternal Mint", amount=70)]  # قیمت پیشنهادی من
        )
        return {"url": link}
    except Exception as e:
        logging.error(f"Invoice error: {e}")
        return {"error": "Failed"}

@dp.pre_checkout_query()
async def checkout_ok(q: types.PreCheckoutQuery):
    await q.answer(ok=True)

@dp.message(F.successful_payment)
async def payment_done(message: types.Message):
    try:
        uid, burden, t_path, use_prof = message.successful_payment.invoice_payload.split(":")
        uid = int(uid)
        final_img = t_path if t_path != "none" else None

        if not final_img and use_prof == "1":
            photos = await bot.get_user_profile_photos(uid, limit=1)
            if photos.total_count > 0:
                f = await bot.get_file(photos.photos[0][-1].file_id)
                dest = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg").name
                await bot.download_file(f.file_path, dest)
                final_img = dest

        nft = create_certificate(uid, burden, photo_path=final_img)

        await bot.send_document(
            uid,
            FSInputFile(nft),
            caption=f"🔱 <b>ASCENDED</b>\nBurden: <i>{burden}</i>\nStatus: Consumed by The Void\n\nYour NFT is eternal.",
            parse_mode="HTML"
        )

        # پاکسازی امن
        for p in [nft, t_path if t_path != "none" else None, final_img]:
            if p and os.path.exists(p):
                try: os.remove(p)
                except: pass
    except Exception as e:
        logging.error(f"Payment handler error: {e}")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/webhook")
async def wh(r: Request):
    upd = Update.model_validate(await r.json(), context={"bot": bot})
    await dp.feed_update(bot, upd)
    return {"ok": True}

@app.on_event("startup")
async def on_start():
    await bot.set_webhook(f"{os.getenv('WEBHOOK_URL')}/webhook")
