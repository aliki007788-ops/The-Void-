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

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
PRICE_BASIC = 70
PRICE_PREMIUM = 120
VIP_FILE = "vip_codes.txt"

def load_vip():
    if os.path.exists(VIP_FILE):
        with open(VIP_FILE, "r") as f:
            return set(line.strip().upper() for line in f)
    return set()

def save_vip(codes):
    with open(VIP_FILE, "w") as f:
        f.write("\n".join(sorted(codes)))

VIP_CODES = load_vip()

async def send_nft(uid: int, burden: str, photo_path: str = None, gift: bool = False):
    nft = create_certificate(uid, burden, photo_path)
    caption = "🔱 <b>DIVINE GIFT</b>" if gift else "🔱 <b>ASCENDED</b>"
    await bot.send_document(uid, FSInputFile(nft), caption=caption, parse_mode="HTML")
    for p in [nft, photo_path]:
        if p and os.path.exists(p):
            os.remove(p)

@dp.message(F.text == "/start")
async def start(msg: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔱 ENTER THE VOID", web_app=WebAppInfo(url=f"{os.getenv('WEBHOOK_URL')}/static/index.html"))
    ]])
    await msg.answer("<b>THE VOID CALLS.</b>\nSacrifice to ascend.", reply_markup=kb, parse_mode="HTML")

@dp.message(F.from_user.id == ADMIN_ID, F.text.startswith("/gen"))
async def gen(msg: types.Message):
    count = int(msg.text.split()[1]) if len(msg.text.split()) > 1 else 1
    codes = [f"VOID-{secrets.token_hex(3).upper()}" for _ in range(count)]
    VIP_CODES.update(codes)
    save_vip(VIP_CODES)
    await msg.answer("New VIP codes:\n" + "\n".join(f"<code>{c}</code>" for c in codes), parse_mode="HTML")

@app.get("/create_stars_invoice")
async def invoice(d: str):
    data = json.loads(base64.b64decode(d).decode())
    burden = data['b'].upper().strip()

    if burden in VIP_CODES:
        VIP_CODES.remove(burden)
        save_vip(VIP_CODES)
        await send_nft(data['u'], f"GIFT: {burden}", None, gift=True)
        return {"free": True}

    premium = bool(data.get('p') or data.get('prof'))
    amount = PRICE_PREMIUM if premium else PRICE_BASIC

    temp = "none"
    if data.get('p'):
        img = base64.b64decode(data['p'].split(',')[1])
        t = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        t.write(img)
        t.close()
        temp = t.name

    payload = f"{data['u']}:{data['b']}:{temp}:{1 if data.get('prof') else 0}"
    link = await bot.create_invoice_link(
        title="VOID ASCENSION",
        description="Divine Imprint" if premium else "Eternal Record",
        payload=payload,
        currency="XTR",
        prices=[LabeledPrice(label="Ascension Fee", amount=amount)]
    )
    return {"url": link}

@dp.pre_checkout_query()
async def pre(q: types.PreCheckoutQuery):
    await q.answer(ok=True)

@dp.message(F.successful_payment)
async def paid(m: types.Message):
    parts = m.successful_payment.invoice_payload.split(":")
    uid = int(parts[0])
    burden = parts[1]
    temp = parts[2] if parts[2] != "none" else None
    prof = parts[3] == "1"
    await send_nft(uid, burden, temp if not prof else None)

app.mount("/static", StaticFiles(directory="static"))

@app.post("/webhook")
async def webhook(r: Request):
    update = Update.model_validate(await r.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.on_event("startup")
async def start():
    await bot.set_webhook(f"{os.getenv('WEBHOOK_URL')}/webhook")
