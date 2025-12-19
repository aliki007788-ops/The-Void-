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

def load_vips():
    if not os.path.exists(VIP_FILE): return set()
    with open(VIP_FILE, "r") as f: return set(line.strip().upper() for line in f if line.strip())

def save_vips(codes):
    with open(VIP_FILE, "w") as f: f.write("\n".join(sorted(codes)))

async def get_tg_photo(uid):
    """دانلود خودکار عکس پروفایل کاربر از تلگرام"""
    try:
        photos = await bot.get_user_profile_photos(uid, limit=1)
        if photos.total_count > 0:
            file = await bot.get_file(photos.photos[0][-1].file_id)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            await bot.download_file(file.file_path, tmp.name)
            return tmp.name
    except: pass
    return None

async def send_final_nft(uid, name, photo_path, is_vip=False):
    """تولید NFT و ارسال به کاربر"""
    nft_path = create_certificate(uid, name, photo_path)
    caption = "🔱 **PARTNER SOUL RECORDED**" if is_vip else "🔱 **ASCENSION COMPLETE**"
    await bot.send_document(uid, FSInputFile(nft_path), caption=caption, parse_mode="Markdown")
    if photo_path and os.path.exists(photo_path): os.remove(photo_path)
    if os.path.exists(nft_path): os.remove(nft_path)

@app.post("/create_stars_invoice")
async def create_invoice(request: Request):
    data = await request.json()
    uid = data['u']
    burden_input = data.get('b', '').strip()
    
    # منطق VIP و استخراج نام بیزنس
    vips = load_vips()
    final_name = burden_input
    is_vip = False
    
    for code in list(vips):
        if burden_input.upper() == code:
            is_vip = True
            vips.remove(code); save_vips(vips)
            if "PARTNER-" in code:
                final_name = code.split("-")[-1] # استخراج نام از انتهای کد
            break

    if is_vip:
        photo = None
        if data.get('prof'): photo = await get_tg_photo(uid)
        elif data.get('p'):
            img_b64 = base64.b64decode(data['p'].split(',')[1])
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            tmp.write(img_b64); tmp.close(); photo = tmp.name
        await send_final_nft(uid, final_name, photo, True)
        return {"free": True}

    # روال عادی پرداخت ستاره
    photo_payload = "profile" if data.get('prof') else ("custom" if data.get('p') else "none")
    custom_photo_path = "none"
    if data.get('p'):
        img_b64 = base64.b64decode(data['p'].split(',')[1])
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        tmp.write(img_b64); tmp.close(); custom_photo_path = tmp.name

    payload = f"{uid}:{burden_input}:{custom_photo_path}:{photo_payload}"
    amount = 120 if (data.get('p') or data.get('prof')) else 70
    
    link = await bot.create_invoice_link(
        title="VOID ASCENSION", description="Your soul imprint in the void.",
        payload=payload, currency="XTR", prices=[LabeledPrice(label="Ascension Fee", amount=amount)]
    )
    return {"url": link}

@dp.message(F.successful_payment)
async def payment_success(m: types.Message):
    p = m.successful_payment.invoice_payload.split(":")
    uid, name, c_path, p_type = int(p[0]), p[1], p[2], p[3]
    
    photo = None
    if p_type == "custom": photo = c_path
    elif p_type == "profile": photo = await get_tg_photo(uid)
    
    await send_final_nft(uid, name, photo)

@dp.message(F.text == "/start")
async def cmd_start(m: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔱 ENTER THE VOID", web_app=WebAppInfo(url=f"{os.getenv('WEBHOOK_URL')}/static/index.html"))
    ]])
    await m.answer("<b>WELCOME TO THE ETERNAL VOID.</b>", reply_markup=kb, parse_mode="HTML")

@dp.message(F.from_user.id == ADMIN_ID, F.text.startswith("/partner"))
async def cmd_partner(m: types.Message):
    name = m.text.replace("/partner", "").strip().upper()
    if not name: return await m.answer("Usage: /partner NIKE")
    code = f"PARTNER-{secrets.token_hex(2).upper()}-{name}"
    vips = load_vips(); vips.add(code); save_vips(vips)
    await m.answer(f"✅ Partner Code Produced:\n<code>{code}</code>", parse_mode="HTML")

app.mount("/static", StaticFiles(directory="static"))
@app.post("/webhook")
async def webhook(r: Request):
    u = Update.model_validate(await r.json(), context={"bot": bot})
    await dp.feed_update(bot, u)
    return {"ok": True}

@app.on_event("startup")
async def startup(): await bot.set_webhook(f"{os.getenv('WEBHOOK_URL')}/webhook")
