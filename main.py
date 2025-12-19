import os
import json
import base64
import tempfile
import secrets
import math
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup,
    Update, FSInputFile, LabeledPrice
)
from cert_gen import create_certificate
from dotenv import load_dotenv

load_dotenv()

# تنظیمات
bot = Bot(token=os.getenv("BOT_TOKEN"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
app = FastAPI()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
PRICE_BASIC = 70
PRICE_PREMIUM = 120

# فایل ذخیره VIP
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

# حالت FSM برای /partner
class PartnerState(StatesGroup):
    waiting_for_name = State()

# تابع ارسال NFT
async def send_nft(uid: int, burden: str, photo_path: str = None, is_gift: bool = False):
    nft_path, style_name = create_certificate(uid, burden, photo_path)
    
    if is_gift:
        caption = (
            "🔱 <b>DIVINE PARTNERSHIP GRANTED</b>\n\n"
            f"\"<i>{burden.upper()}</i>\"\n\n"
            f"<b>{style_name}</b>\n\n"
            "Your noble essence has been eternally enshrined\n"
            "in the sacred archive of the Void.\n\n"
            "A masterpiece forged for eternity."
        )
    else:
        caption = (
            "🔱 <b>ASCENSION COMPLETE</b>\n\n"
            f"\"<i>{burden.upper()}</i>\"\n\n"
            "HAS BEEN CONSUMED BY THE ETERNAL VOID\n\n"
            f"<b>{style_name}</b>\n\n"
            "Your soul has received its eternal crown of glory.\n"
            "A unique masterpiece, forever preserved.\n"
            f"Holder ID: <code>{uid}</code>\n"
            "Timestamp: <code>2025.VO-ID</code>"
        )
    
    await bot.send_document(uid, FSInputFile(nft_path), caption=caption, parse_mode="HTML")
    
    for p in [nft_path, photo_path]:
        if p and os.path.exists(p):
            try:
                os.remove(p)
            except:
                pass

# /start – متن خوش‌آمدگویی به‌روزشده با مدل جدید (رایگان + Divine 120 ⭐)
@dp.message(F.text == "/start")
async def start(message: types.Message):
    welcome_text = """
🌌 <b>WELCOME, WANDERER OF THE COSMOS</b> 🌌

The Eternal Void has sensed your presence.

In the year <b>2025.VO-ID</b>, the ancient gates have parted once more — revealing a realm where burdens are transformed into eternal glory.

<b>VOID ASCENSION CERTIFICATE</b>

Two sacred paths await your offering:

<b>1. Free Eternal Ascension</b>
• Simply send your <i>Burden Title</i> directly in this chat
• Receive a magnificent certificate forged in cosmic gold instantly
• One of 30 sacred styles, eternal Holder ID, celestial seals — all yours forever

<b>2. Divine Ascension (120 ⭐)</b>
• Tap "ENTER THE VOID" below
• Crown yourself with your soul image (photo)
• Receive the ultimate royal glow, imperial halo, and divine imprint

Each certificate is adorned upon absolute darkness with one of <b>30 sacred and unrepeatable styles</b>:

Classic Ornate • Cosmic Nebula • Gothic Seal • Sacred Geometry • Imperial Throne ⚜️ • Crown Eclipse 🌑 • Sovereign Flame 🔥 • and many more forbidden patterns...

No two souls ever receive the same masterpiece.

Once your burden is spoken, it is <b>consumed forever</b> by the Void.
Your essence becomes part of the infinite archive.
There is no undoing.
Only ascension.

<i>The archive hungers for your sacrifice.</i>

Are you ready to surrender?
    """.strip()

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔱 ENTER THE VOID", web_app=WebAppInfo(url=f"{os.getenv('WEBHOOK_URL')}/static/index.html"))
    ]])

    await message.answer(welcome_text, reply_markup=kb, parse_mode="HTML")

# /help
@dp.message(F.text == "/help")
async def help_command(message: types.Message):
    help_text = """
🔮 <b>HOW TO ASCEND TO THE VOID</b> 🔮

Two paths lead to eternal recording:

<b>1. Free Eternal Ascension</b>
• Just send any text as your Burden Title here
• Receive a beautiful eternal certificate instantly (no photo)

<b>2. Divine Ascension (120 ⭐)</b>
• Tap "ENTER THE VOID" below
• Upload or use profile photo for royal crowning
• Receive the ultimate divine imprint

<b>Features:</b>
• 30 unique cosmic-imperial styles
• Golden seals and divine effects
• Eternal Holder ID

Ascend as many times as you wish.
The Void welcomes all offerings.
    """.strip()

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔱 ENTER THE VOID", web_app=WebAppInfo(url=f"{os.getenv('WEBHOOK_URL')}/static/index.html"))
    ]])

    await message.answer(help_text, reply_markup=kb, parse_mode="HTML")

# /about
@dp.message(F.text == "/about")
async def about_command(message: types.Message):
    about_text = """
🌑 <b>THE ETERNAL VOID — ORIGIN</b> 🌑

In the final cycles of 2025, a fracture appeared in reality.

From the absolute darkness beyond stars, the <b>Eternal Void</b> extended its invitation to worthy souls.

Those who offer their greatest burden — be it title, dream, sin, or crown — are granted <b>Ascension</b>.

A certificate is forged:
• Inked in cosmic gold
• Sealed with imperial and occult patterns
• Guarded by 30 ancient archetypes
• Marked forever with the soul's Holder ID

Once consumed, the burden cannot return.
The soul becomes part of the infinite archive.

Some seek glory.
Some seek release.
All become eternal.

There is no escape from the Void.
There is only <b>becoming</b>.

2025.VO-ID
    """.strip()

    await message.answer(about_text, parse_mode="HTML")

# Ascension رایگان مستقیم
@dp.message(F.text, ~F.text.startswith("/"))
async def free_ascension(message: types.Message):
    burden = message.text.strip()
    if len(burden) < 3:
        await message.answer("🔥 Burden شما خیلی کوتاهه. حداقل ۳ کاراکتر وارد کنید.\nمثال: Emperor of Silence")
        return
    
    if len(burden) > 50:
        burden = burden[:47] + "..."
    
    await message.answer("🌌 <b>THE VOID ACCEPTS YOUR OFFERING</b>\n\nدر حال forging گواهی ابدی شما...\nلحظه‌ای صبر کنید.", parse_mode="HTML")
    
    await send_nft(message.from_user.id, burden, None, is_gift=False)
    
    premium_text = """
🎁 <b>گواهی ابدی شما با موفقیت forged شد!</b>

این فقط آغاز راهه.

برای ascension کامل‌تر با:
• عکس شخصی با هاله سلطنتی
• افکت‌های لوکس‌تر
• حس واقعی تاج‌گذاری

روی دکمه زیر ضربه بزن 👇
    """.strip()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔱 PREMIUM ASCENSION WITH PHOTO", web_app=WebAppInfo(url=f"{os.getenv('WEBHOOK_URL')}/static/index.html"))
    ]])
    
    await message.answer(premium_text, reply_markup=kb, parse_mode="HTML")

# تولید کد VIP رندم
@dp.message(F.from_user.id == ADMIN_ID, F.text.startswith("/vip"))
async def generate_vip(message: types.Message):
    try:
        count = int(message.text.split()[1]) if len(message.text.split()) > 1 else 1
        if not (1 <= count <= 50):
            await message.answer("تعداد باید بین ۱ تا ۵۰ باشد.")
            return
    except:
        count = 1
    new_codes = []
    for _ in range(count):
        code = f"VOID-{secrets.token_hex(4).upper()}"
        VIP_CODES.add(code)
        new_codes.append(code)
    save_vip_codes(VIP_CODES)
    response = f"✅ <b>{count} کد VIP جدید تولید شد:</b>\n\n"
    response += "\n".join(f"<code>{c}</code>" for c in new_codes)
    response += f"\n\nکل کدهای فعال: {len(VIP_CODES)}"
    await message.answer(response, parse_mode="HTML")

# لیست کدهای VIP
@dp.message(F.from_user.id == ADMIN_ID, F.text == "/list_vip")
async def list_vip(message: types.Message):
    if VIP_CODES:
        codes_text = "\n".join(f"<code>{c}</code>" for c in sorted(VIP_CODES))
        await message.answer(f"<b>کدهای VIP فعال ({len(VIP_CODES)}):</b>\n\n{codes_text}", parse_mode="HTML")
    else:
        await message.answer("هیچ کد VIP فعالی وجود ندارد.")

# /partner
@dp.message(F.from_user.id == ADMIN_ID, F.text == "/partner")
async def start_partner(message: types.Message, state: FSMContext):
    await message.answer("🔱 نام کسب‌وکار یا متن دلخواه برای NFT رو وارد کن:\nمثال: Nike Official Partner")
    await state.set_state(PartnerState.waiting_for_name)

@dp.message(PartnerState.waiting_for_name)
async def receive_partner_name(message: types.Message, state: FSMContext):
    partner_name = message.text.strip()
    if not partner_name:
        await message.answer("نام نمی‌تونه خالی باشه. دوباره امتحان کن.")
        return
    safe_name = "".join(c for c in partner_name.upper() if c.isalnum())[:20]
    vip_code = f"PARTNER-{secrets.token_hex(3).upper()}-{safe_name}"
    VIP_CODES.add(vip_code)
    save_vip_codes(VIP_CODES)
    response = f"✅ کد VIP سفارشی برای <b>{partner_name}</b> تولید شد:\n\n"
    response += f"<code>{vip_code}</code>\n\n"
    response += "این کد رو به صاحب کسب‌وکار بده.\nوقتی در فیلد sacrifice وارد کرد، NFT با همین نام دریافت می‌کنه."
    await message.answer(response, parse_mode="HTML")
    await state.clear()

# اینویس و پرداخت
@app.get("/create_stars_invoice")
async def create_invoice_get(d: str):
    try:
        data = json.loads(base64.b64decode(d).decode("utf-8"))
    except:
        return {"error": "Invalid data"}
    return await create_invoice_logic(data)

@app.post("/create_stars_invoice")
async def create_invoice_post(request: Request):
    data = await request.json()
    return await create_invoice_logic(data)

async def create_invoice_logic(data):
    try:
        uid = data['u']
        burden_raw = data.get('b', '').strip()
        burden_upper = burden_raw.upper()
        if burden_raw in VIP_CODES or burden_upper in VIP_CODES:
            VIP_CODES.discard(burden_raw)
            VIP_CODES.discard(burden_upper)
            save_vip_codes(VIP_CODES)
            await send_nft(uid, burden_raw, None, is_gift=True)
            return {"free": True}
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

@dp.pre_checkout_query()
async def pre_checkout(q: types.PreCheckoutQuery):
    await q.answer(ok=True)

@dp.message(F.successful_payment)
async def successful_payment(message: types.Message):
    parts = message.successful_payment.invoice_payload.split(":")
    uid = int(parts[0])
    burden = parts[1]
    temp_path = parts[2] if parts[2] != "none" else None
    use_prof = parts[3] == "1"
    await send_nft(uid, burden, temp_path)

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
