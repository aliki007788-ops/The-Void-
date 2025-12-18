import os, json, base64, tempfile, secrets
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, Update, FSInputFile, LabeledPrice
from cert_gen import create_certificate
from dotenv import load_dotenv

# بارگذاری تنظیمات
load_dotenv()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
app = FastAPI()

# تنظیمات ادمین و کدهای VIP
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
VIP_CODES = set()

# فایل ذخیره‌سازی کدها برای جلوگیری از پاک شدن با ریستارت سرور
VIP_FILE = "active_vip_codes.txt"

def save_codes():
    with open(VIP_FILE, "w") as f:
        f.write("\n".join(VIP_CODES))

def load_codes():
    if os.path.exists(VIP_FILE):
        with open(VIP_FILE, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

# بارگذاری اولیه کدها
VIP_CODES = load_codes()

# --- بخش مدیریت فایل و ارسال NFT ---
async def process_and_send_nft(uid, burden, t_path, use_prof, is_gift=False):
    final_img = t_path if t_path != "none" else None
    
    # اگر کاربر تیک پروفایل را زده باشد
    if not final_img and use_prof == "1":
        photos = await bot.get_user_profile_photos(int(uid), limit=1)
        if photos.total_count > 0:
            f = await bot.get_file(photos.photos[0][-1].file_id)
            dest = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg").name
            await bot.download_file(f.file_path, dest)
            final_img = dest

    # تولید گواهی توسط موتور گرافیکی
    nft_path = create_certificate(uid, burden, final_img)
    
    caption = "🔱 <b>DIVINE GIFT GRANTED</b>\nYour business ascension is complete." if is_gift else "🔱 <b>IT IS DONE.</b>\nYou have transcended."
    await bot.send_document(int(uid), FSInputFile(nft_path), caption=caption, parse_mode="HTML")
    
    # پاکسازی فایل‌ها
    for path in [nft_path, t_path, final_img]:
        if path and os.path.exists(path) and path != "none":
            try: os.remove(path)
            except: pass

# --- بخش دستورات تلگرام ---
@dp.message(F.text == "/start")
async def start(m: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔱 ENTER THE VOID", web_app=WebAppInfo(url=f"{os.getenv('WEBHOOK_URL')}/static/index.html"))
    ]])
    await m.answer(
        "<b>WELCOME TO THE ETERNAL VOID.</b>\nSacrifice your burdens and achieve digital immortality.",
        reply_markup=kb, parse_mode="HTML"
    )

@dp.message(F.from_user.id == ADMIN_ID, F.text == "/gen_code")
async def generate_vip_code(m: types.Message):
    new_code = f"VOID-{secrets.token_hex(2).upper()}"
    VIP_CODES.add(new_code)
    save_codes()
    await m.answer(f"✅ <b>NEW VIP CODE CREATED:</b>\n<code>{new_code}</code>\n\nOne-time use only.", parse_mode="HTML")

# --- بخش API و پرداخت ---
@app.get("/create_stars_invoice")
async def invoice(d: str):
    data = json.loads(base64.b64decode(d).decode('utf-8'))
    user_input = data.get('b', '').upper().strip()
    
    # بررسی کد VIP
    if user_input in VIP_CODES:
        VIP_CODES.remove(user_input)
        save_codes()
        await process_and_send_nft(data['u'], f"VIP: {user_input}", "none", "0", is_gift=True)
        return {"free": True}

    # تعیین قیمت بر اساس وجود تصویر
    is_premium = True if (data.get('p') or data.get('prof')) else False
    amount = 120 if is_premium else 70
    
    t_path = "none"
    if data.get('p'):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(base64.b64decode(data['p'].split(",")[1]))
            t_path = tmp.name

    payload = f"{data['u']}:{data['b']}:{t_path}:{1 if data.get('prof') else 0}"
    
    title = "DIVINE VOID NFT" if is_premium else "ETERNAL VOID NFT"
    desc = "Premium Visual Soul Imprinting" if is_premium else "Eternal Record of Sacrifice"

    link = await bot.create_invoice_link(
        title=title, description=desc, payload=payload,
        currency="XTR", prices=[LabeledPrice(label="Minting Fee", amount=amount)]
    )
    return {"url": link}

@dp.pre_checkout_query()
async def checkout(q: types.PreCheckoutQuery):
    await q.answer(ok=True)

@dp.message(F.successful_payment)
async def paid(m: types.Message):
    uid, burden, t_path, use_prof = m.successful_payment.invoice_payload.split(":")
    await process_and_send_nft(uid, burden, t_path, use_prof)

# --- تنظیمات سرور ---
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/webhook")
async def wh(r: Request):
    upd = Update.model_validate(await r.json(), context={"bot": bot})
    await dp.feed_update(bot, upd)
    return {"ok": True}
