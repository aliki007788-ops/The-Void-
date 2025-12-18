import os, json, base64, tempfile, logging
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

GIFT_CODE = "VOID-FREE"

async def process_and_send_nft(uid, burden, t_path, use_prof, is_gift=False):
    final_img = t_path if t_path != "none" else None
    if not final_img and use_prof == "1":
        photos = await bot.get_user_profile_photos(int(uid), limit=1)
        if photos.total_count > 0:
            f = await bot.get_file(photos.photos[0][-1].file_id)
            dest = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg").name
            await bot.download_file(f.file_path, dest)
            final_img = dest

    nft = create_certificate(uid, burden, final_img)
    caption = "🔱 <b>GIFT FROM THE VOID</b>" if is_gift else "🔱 <b>ASCENDED</b>"
    await bot.send_document(int(uid), FSInputFile(nft), caption=caption, parse_mode="HTML")
    
    for p in [nft, t_path, final_img]:
        if p and os.path.exists(p) and p != "none":
            try: os.remove(p)
            except: pass

@app.get("/create_stars_invoice")
async def invoice(d: str):
    data = json.loads(base64.b64decode(d).decode('utf-8'))
    is_premium = True if (data.get('p') or data.get('prof')) else False
    
    if data.get('b').upper() == GIFT_CODE:
        await process_and_send_nft(data['u'], data['b'], "none", "0", is_gift=True)
        return {"free": True}

    amount = 120 if is_premium else 70
    t_path = "none"
    if data.get('p'):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(base64.b64decode(data['p'].split(",")[1]))
            t_path = tmp.name

    payload = f"{data['u']}:{data['b']}:{t_path}:{1 if data.get('prof') else 0}"
    link = await bot.create_invoice_link(
        title="VOID ASCENSION",
        description="Divine Grade NFT" if is_premium else "Eternal Grade NFT",
        payload=payload, currency="XTR", 
        prices=[LabeledPrice(label="Minting Fee", amount=amount)]
    )
    return {"url": link}

@dp.message(F.successful_payment)
async def payment_ok(m: types.Message):
    uid, burden, t_path, use_prof = m.successful_payment.invoice_payload.split(":")
    await process_and_send_nft(uid, burden, t_path, use_prof)

app.mount("/static", StaticFiles(directory="static"), name="static")
@app.post("/webhook")
async def wh(r: Request):
    upd = Update.model_validate(await r.json(), context={"bot": bot})
    await dp.feed_update(bot, upd)
    return {"ok": True}
