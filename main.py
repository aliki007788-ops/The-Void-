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

@dp.message(F.text == "/start")
async def start(m: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔱 SACRIFICE", web_app=WebAppInfo(url=f"{os.getenv('WEBHOOK_URL')}/static/index.html"))
    ]])
    await m.answer("<b>THE VOID IS HUNGRY.</b>", reply_markup=kb, parse_mode="HTML")

@app.get("/create_stars_invoice")
async def invoice(d: str):
    data = json.loads(base64.b64decode(d).decode('utf-8'))
    t_path = "none"
    if data.get('p'):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(base64.b64decode(data['p'].split(",")[1]))
            t_path = tmp.name

    payload = f"{data['u']}:{data['b']}:{t_path}:{1 if data.get('prof') else 0}"
    link = await bot.create_invoice_link(
        title="VOID NFT PRESTIGE",
        description=f"Sacrifice: {data['b']}",
        payload=payload, currency="XTR", prices=[LabeledPrice(label="Mint", amount=70)]
    )
    return {"url": link}

@dp.pre_checkout_query()
async def checkout(q: types.PreCheckoutQuery): await q.answer(ok=True)

@dp.message(F.successful_payment)
async def paid(m: types.Message):
    uid, burden, t_path, use_prof = m.successful_payment.invoice_payload.split(":")
    final_img = t_path if t_path != "none" else None
    
    if not final_img and use_prof == "1":
        photos = await bot.get_user_profile_photos(int(uid), limit=1)
        if photos.total_count > 0:
            f = await bot.get_file(photos.photos[0][-1].file_id)
            dest = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg").name
            await bot.download_file(f.file_path, dest)
            final_img = dest

    nft = create_certificate(uid, burden, final_img)
    await bot.send_document(int(uid), FSInputFile(nft), caption="🔱 ASCENDED.")
    
    for p in [nft, t_path, final_img]:
        if p and os.path.exists(p) and p != "none": os.remove(p)

app.mount("/static", StaticFiles(directory="static"), name="static")
@app.post("/webhook")
async def wh(r: Request):
    upd = Update.model_validate(await r.json(), context={"bot": bot})
    await dp.feed_update(bot, upd)
    return {"ok": True}
