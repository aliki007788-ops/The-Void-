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

# تنظیمات ادمین و قیمت
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
PRICE_BASIC = 70
PRICE_PREMIUM = 120

# فایل ذخیره کدهای VIP (دائمی حتی با ریستارت)
VIP_FILE = "vip_codes.txt"

def load_vip_codes():
    if os.path.exists(VIP_FILE):
        with open(VIP_FILE, "r", encoding="utf-8") as f:
            return set(line.strip().upper() for line in f if line.strip())
    return set()

def save_vip_codes(codes):
    with open(VIP_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(codes)))

VIP_CODES = load_vip_codes()

async def send_nft(uid: int, burden: str, photo_path: str = None, is_gift: bool = False):
    nft = create_certificate(uid, burden, photo_path)
    caption = "🔱 <b>DIVINE GIFT GRANTED</b>\nYour ascension is eternal." if is_gift else "🔱 <b>ASCENSION COMPLETE</b>\nYour sacrifice has been consumed."
    await bot.send_document(uid, FSInputFile(nft), caption=caption, parse_mode="HTML")

    # پاکسازی فایل‌ها
    for path in [nft, photo_path]:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass

# دستور /start
@dp.message(F.text == "/start")
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔱 ENTER THE VOID", web_app=WebAppInfo(url=f"{os.getenv('WEBHOOK_URL')}/static/index.html"))
    ]])
    await message.answer("<b>WELCOME TO THE ETERNAL VOID.</b>\nSacrifice to ascend.", reply_markup=kb, parse_mode="HTML")

# دستور تولید کد VIP برای ادمین
@dp.message(F.from_user.id == ADMIN_ID, F.text.startswith("/vip"))
async def generate_vip(message: types.Message):
    try:
        count = int(message.text.split()[1]) if len(message.text.split()) > 1 else 1
        if count > 50:
            await message.answer("حداکثر ۵۰ کد در یک بار.")
            return
    except:
        count = 1

    new_codes = []
    for _ in range(count):
        code = f"VOID-{secrets.token_hex(4).upper()}"  # ۸ کاراکتر خیلی امن
        VIP_CODES.add(code)
        new_codes.append(code)

    save_vip_codes(VIP_CODES)

    response = f"✅ <b>{count} کد VIP جدید تولید شد:</b>\n\n"
    response += "\n".join(f"<code>{c}</code>" for c in new_codes)
    response += f"\n\nکل کدهای فعال: {len(VIP_CODES)}"

    await message.answer(response, parse_mode="HTML")

# لیست کدهای فعال
@dp.message(F.from_user.id == ADMIN_ID, F.text == "/list_vip")
async def list_vip(message: types.Message):
    if VIP_CODES:
        codes_text = "\n".join(f"<code>{c}</code>" for c in sorted(VIP_CODES))
        await message.answer(f"<b>کدهای VIP فعال ({len(VIP_CODES)}):</b>\n\n{codes_text}", parse_mode="HTML")
    else:
        await message.answer("هیچ کد VIP فعالی وجود ندارد.")

# ایجاد اینویس
@app.get("/create_stars_invoice")
async def create_invoice(d: str):
    try:
        data = json.loads(base64.b64decode(d).decode("utf-8"))
        uid = data['u']
        burden_upper = data.get('b', '').upper().strip()

        # چک کد VIP
        if burden_upper in VIP_CODES:
            VIP_CODES.remove(burden_upper)
            save_vip_codes(VIP_CODES)
            await send_nft(uid, data['b'], None, is_gift=True)
            return {"free": True}

        # حالت عادی
        is_premium = bool(data.get('p') or data.get('prof'))
        amount = PRICE_PREMIUM if is_premium else PRICE_BASIC

        temp_path = "none"
        if data.get('p'):
            img_data = base64.b64decode(data['p'].split(',')[1])
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            tmp.write(img_data)
            tmp.close()
            temp_path = tmp.name

        payload = f"{uid}:{data['b']}:{temp_path}:{1 if data.get('prof') else 0}"

        link = await bot.create_invoice_link(
            title="VOID ASCENSION",
            description="Divine Soul Imprint" if is_premium else "Eternal Sacrifice",
            payload=payload,
            currency="XTR",
            prices=[LabeledPrice(label="Ascension Fee", amount=amount)]
        )
        return {"url": link}

    except Exception as e:
        print("Invoice error:", e)
        return {"error": "The Void is unreachable"}

# پرداخت
@dp.pre_checkout_query()
async def pre_checkout(q: types.PreCheckoutQuery):
    await q.answer(ok=True)

@dp.message(F.successful_payment)
async def successful_payment(message: types.Message):
    payload = message.successful_payment.invoice_payload.split(":")
    uid = int(payload[0])
    burden = payload[1]
    temp_path = payload[2] if payload[2] != "none" else None
    use_prof = payload[3] == "1"

    # اگر تیک پروفایل زده شده، عکس رو بگیر (اختیاری)
    photo = temp_path
    if use_prof and not temp_path:
        # کد گرفتن عکس پروفایل (اختیاری – اگر بخوای اضافه کن)
        pass

    await send_nft(uid, burden, photo)

# وب‌هوک
app.mount("/static", StaticFiles(directory="static"))

@app.post("/webhook")
async def webhook(request: Request):
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.on_event("startup")
async def startup():
    await bot.set_webhook(f"{os.getenv('WEBHOOK_URL')}/webhook")
