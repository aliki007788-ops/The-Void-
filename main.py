import os, json, base64, tempfile, secrets
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Update, FSInputFile, LabeledPrice, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from cert_gen import create_certificate
from dotenv import load_dotenv

load_dotenv()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
app = FastAPI()

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
VIP_FILE = "vip_codes.txt"

def get_vips():
    if not os.path.exists(VIP_FILE): return set()
    with open(VIP_FILE, "r") as f: return set(line.strip().upper() for line in f if line.strip())

def save_vips(codes):
    with open(VIP_FILE, "w") as f: f.write("\n".join(codes))

async def get_tg_photo(uid):
    """دریافت عکس پروفایل کاربر از تلگرام"""
    try:
        photos = await bot.get_user_profile_photos(uid, limit=1)
        if photos.total_count > 0:
            file = await bot.get_file(photos.photos[0][-1].file_id)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            await bot.download_file(file.file_path, tmp.name)
            return tmp.name
    except: pass
    return None

async def process_and_send(uid, name, photo_path, is_vip=False):
    """تولید و ارسال نهایی NFT"""
    final_path = create_certificate(uid, name, photo_path)
    cap = "🔱 **PARTNER ASCENSION**" if is_vip else "🔱 **ASCENSION COMPLETE**"
    await bot.send_document(uid, FSInputFile(final_path), caption=cap, parse_mode="Markdown")
    if photo_path and os.path.exists(photo_path): os.remove(photo_path)
    if os.path.exists(final_path): os.remove(final_path)

@app.post("/create_stars_invoice")
async def handle_invoice(request: Request):
    data = await request.json()
    uid = data.get('u')
    burden_input = data.get('b', '').strip()
    
    # منطق VIP و استخراج نام بیزنس
    vips = get_vips()
    is_vip = False
    display_name = burden_input
    
    for code in list(vips):
        if burden_input.upper() == code:
            is_vip = True
            vips.remove(code)
            save_vips(vips)
            if "PARTNER-" in code:
                # استخراج Nike از PARTNER-HEX-NIKE
                display_name = code.split("-")[-1]
            break

    if is_vip:
        photo = await get_tg_photo(uid) if data.get('prof') else None
        if data.get('p'): # اگر عکس آپلود کرده بود
            img = base64.b64decode(data['p'].split(',')[1])
            t = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            t.write(img); t.close(); photo = t.name
        await process_and_send(uid, display_name, photo, True)
        return {"free": True}

    # روال عادی پرداخت
    photo_type = "profile" if data.get('prof') else ("custom" if data.get('p') else "none")
    custom_path = "none"
    if data.get('p'):
        img = base64.b64decode(data['p'].split(',')[1])
        t = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        t.write(img); t.close(); custom_path = t.name

    payload = f"{uid}:{burden_input}:{custom_path}:{photo_type}"
    amount = 120 if (data.get('p') or data.get('prof')) else 70
    
    link = await bot.create_invoice_link(
        title="VOID ASCENSION", description="Eternal Imprint",
        payload=payload, currency="XTR", prices=[LabeledPrice(label="Fee", amount=amount)]
    )
    return {"url": link}

@dp.message(F.successful_payment)
async def on_pay(m: types.Message):
    p = m.successful_payment.invoice_payload.split(":")
    uid, name, c_path, p_type = int(p[0]), p[1], p[2], p[3]
    
    final_img = None
    if p_type == "custom": final_img = c_path
    elif p_type == "profile": final_img = await get_tg_photo(uid)
    
    await process_and_send(uid, name, final_img)

@dp.message(F.text == "/start")
async def start(m: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔱 ENTER THE VOID", web_app=WebAppInfo(url=f"{os.getenv('WEBHOOK_URL')}/static/index.html"))
    ]])
    await m.answer("WELCOME TO THE VOID.", reply_markup=kb)

# دستور تولید کد بیزنسی برای ادمین
@dp.message(F.from_user.id == ADMIN_ID, F.text.startswith("/partner"))
async def make_partner(m: types.Message):
    name = m.text.replace("/partner", "").strip().upper()
    if not name: return await m.answer("Usage: /partner NIKE")
    code = f"PARTNER-{secrets.token_hex(2).upper()}-{name}"
    vips = get_vips(); vips.add(code); save_vips(vips)
    await m.answer(f"✅ Partner Code:\n`{code}`", parse_mode="MarkdownV2")

app.mount("/static", StaticFiles(directory="static"))
@app.post("/webhook")
async def web_h(r: Request):
    u = Update.model_validate(await r.json(), context={"bot": bot})
    await dp.feed_update(bot, u)
    return {"ok": True}

@app.on_event("startup")
async def on_st(): await bot.set_webhook(f"{os.getenv('WEBHOOK_URL')}/webhook")
