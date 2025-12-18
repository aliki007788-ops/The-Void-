import os, json, base64, tempfile, secrets
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

# تنظیمات ادمین و قیمت‌ها
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
PRICE_BASIC = 70
PRICE_PREMIUM = 120
VIP_FILE = "active_vip_codes.txt"

def save_codes(codes):
    with open(VIP_FILE, "w") as f: f.write("\n".join(codes))

def load_codes():
    if os.path.exists(VIP_FILE):
        with open(VIP_FILE, "r") as f: return set(line.strip() for line in f if line.strip())
    return set()

VIP_CODES = load_codes()

async def process_and_send_nft(uid, burden, t_path, use_prof, is_gift=False):
    final_img = t_path if t_path != "none" else None
    if not final_img and use_prof == "1":
        photos = await bot.get_user_profile_photos(int(uid), limit=1)
        if photos.total_count > 0:
            f = await bot.get_file(photos.photos[0][-1].file_id)
            dest = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg").name
            await bot.download_file(f.file_path, dest)
            final_img = dest

    nft_path = create_certificate(uid, burden, final_img)
    caption = "🔱 <b>DIVINE GIFT GRANTED</b>" if is_gift else "🔱 <b>ASCENDED</b>"
    await bot.send_document(int(uid), FSInputFile(nft_path), caption=caption, parse_mode="HTML")
    for p in [nft_path, t_path, final_img]:
        if p and os.path.exists(p) and p != "none": os.remove(p)

@dp.message(F.text == "/start")
async def start(m: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔱 ENTER THE VOID", web_app=WebAppInfo(url=f"{os.getenv('WEBHOOK_URL')}/static/index.html"))]])
    await m.answer("<b>WELCOME TO THE ETERNAL VOID.</b>", reply_markup=kb, parse_mode="HTML")

@dp.message(F.from_user.id == ADMIN_ID, F.text == "/gen_code")
async def gen_code(m: types.Message):
    new_code = f"VOID-{secrets.token_hex(2).upper()}"
    VIP_CODES.add(new_code)
    save_codes(VIP_CODES)
    await m.answer(f"✅ <b>NEW VIP CODE:</b>\n<code>{new_code}</code>", parse_mode="HTML")

@dp.message(F.from_user.id == ADMIN_ID, F.text == "/list_codes")
async def list_codes(m: types.Message):
    if VIP_CODES:
        await m.answer(f"<b>ACTIVE CODES:</b>\n<code>" + "\n".join(VIP_CODES) + "</code>", parse_mode="HTML")
    else: await m.answer("No active codes.")

@app.get("/create_stars_invoice")
async def invoice(d: str):
    data = json.loads(base64.b64decode(d).decode('utf-8'))
    u_inp = data.get('b', '').upper().strip()
    
    if u_inp in VIP_CODES:
        VIP_CODES.remove(u_inp)
        save_codes(VIP_CODES)
        await process_and_send_nft(data['u'], f"Partner: {u_inp[5:]}", "none", "0", is_gift=True)
        return {"free": True}

    is_premium = True if (data.get('p') or data.get('prof')) else False
    amount = PRICE_PREMIUM if is_premium else PRICE_BASIC
    
    t_path = "none"
    if data.get('p'):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(base64.b64decode(data['p'].split(",")[1]))
            t_path = tmp.name

    payload = f"{data['u']}:{data['b']}:{t_path}:{1 if data.get('prof') else 0}"
    link = await bot.create_invoice_link(title="VOID NFT", description="Ascension Fee", payload=payload, currency="XTR", prices=[LabeledPrice(label="Mint", amount=amount)])
    return {"url": link}

@dp.pre_checkout_query()
async def checkout(q: types.PreCheckoutQuery): await q.answer(ok=True)

@dp.message(F.successful_payment)
async def paid(m: types.Message):
    uid, burden, t_path, use_prof = m.successful_payment.invoice_payload.split(":")
    await process_and_send_nft(uid, burden, t_path, use_prof)

app.mount("/static", StaticFiles(directory="static"), name="static")
@app.post("/webhook")
async def wh(r: Request):
    upd = Update.model_validate(await r.json(), context={"bot": bot})
    await dp.feed_update(bot, upd)
    return {"ok": True}
