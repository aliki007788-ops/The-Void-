import os
import random
import asyncio
import logging
import sqlite3
import requests
import base64
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, BufferedInputFile
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- تنظیمات ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing!")

if not HF_API_TOKEN:
    logger.warning("HF_API_TOKEN missing - AI image generation disabled (fallback used)")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

WEBAPP_URL = "https://the-void-1.onrender.com"
HF_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
OUTPUT_DIR = os.path.join(STATIC_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- دیتابیس ---
def init_db():
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY,
                 username TEXT,
                 refs INTEGER DEFAULT 0,
                 free_mints INTEGER DEFAULT 3,
                 total_ascensions INTEGER DEFAULT 0
              )""")
    c.execute("""CREATE TABLE IF NOT EXISTS ascensions (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 plan TEXT,
                 burden TEXT,
                 dna INTEGER,
                 image_url TEXT,
                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
              )""")
    conn.commit()
    conn.close()

init_db()

# --- پیام خوش‌آمدگویی ---
WELCOME_MESSAGE = (
    "<b>🌌 Emperor of the Eternal Void, the cosmos summons you...</b>\n\n"
    "In the infinite depths of darkness, where stars have long faded and time itself has surrendered,\n"
    "<b>The Void</b> awaits your arrival — only the chosen few dare to ascend to immortality.\n\n"
    "Name your burden.\n"
    "Burn it in golden flames.\n"
    "And rise as the sovereign ruler of the eternal realm.\n\n"
    "Each ascension grants you a unique, forever-irreplaceable certificate — forged in celestial gold, "
    "sealed with the light of dead stars, bearing one of 30 rare imperial styles, and eternally tied to your soul.\n\n"
    "Only the boldest spirits step forward.\n"
    "<b>Are you one of them?</b>\n\n"
    "🔱 <b>Enter The Void now and claim your eternal crown.</b>\n\n"
    "This is not merely a journey.\n"
    "<b>This is the beginning of your everlasting reign.</b>\n\n"
    "<i>The Void bows to no one... except you.</i>"
)

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or "Unknown"
    
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not c.fetchone():
        c.execute("INSERT INTO users (id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()
    conn.close()
    
    bot_username = (await bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    story_link = f"https://t.me/{bot_username}?startapp={user_id}"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌌 ENTER THE VOID", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="👥 Share Referral Link", url=ref_link)],
        [InlineKeyboardButton(text="📱 Add to Story (Share App)", url=story_link)]
    ])
    
    full_msg = WELCOME_MESSAGE + f"\n\n🔗 <b>Your Referral Link:</b>\n<code>{ref_link}</code>\n\nInvite 6 worthy souls and your next ascension will be free."
    await message.answer(full_msg, parse_mode=ParseMode.HTML, reply_markup=kb)

# --- تولید تصویر با Hugging Face ---
async def generate_ai_image(prompt: str, init_image_base64: str = None):
    if not HF_API_TOKEN:
        return None
    API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "strength": 0.4 if init_image_base64 else 0.0,
            "guidance_scale": 8.5,
            "num_inference_steps": 50
        }
    }
    if init_image_base64:
        payload["init_image"] = init_image_base64
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=90)
        if response.status_code == 200:
            return response.content
        logger.error(f"HF API Error: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"HF Request failed: {e}")
    return None

# --- تابع مینت اصلی ---
async def manual_mint(user_id: int, plan: str, burden: str = "Emperor's Gift", photo_base64: str = None):
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    
    prompt = "luxurious dark royal portrait certificate with ornate golden arabesque frame, intricate diamonds and jewels, cosmic nebula background, sacred geometry mandala, elegant ancient gold font, ultra-detailed masterpiece cinematic lighting, 8K quality"
    
    image_bytes = None
    if photo_base64:
        image_bytes = await generate_ai_image(prompt, photo_base64)
    
    if not image_bytes:
        # Fallback لوکس با Pillow
        img = Image.new('RGB', (1000, 1400), (5, 5, 5))
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 950, 1350], outline=(212, 175, 55), width=15)
        draw.rectangle([70, 70, 930, 1330], outline=(169, 135, 0), width=5)
        try:
            font = ImageFont.truetype("arial.ttf", 80)
            font_small = ImageFont.truetype("arial.ttf", 60)
        except:
            font = ImageFont.load_default(size=80)
            font_small = ImageFont.load_default(size=60)
        
        draw.text((500, 200), "THE VOID", fill=(255, 215, 0), font=font, anchor="mm")
        draw.text((500, 400), f"{plan.upper()} ASCENSION", fill=(212, 175, 55), font=font, anchor="mm")
        draw.text((500, 700), f"Burden: {burden}", fill=(240, 240, 240), font=font_small, anchor="mm")
        dna = random.randint(1000000, 9999999)
        draw.text((500, 900), f"DNA: {dna}", fill=(169, 135, 0), font=font_small, anchor="mm")
        draw.text((500, 1100), "Forever consumed by The Void", fill=(100, 100, 100), font=font_small, anchor="mm")
        
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        image_bytes = buffer.getvalue()
    
    filename = f"{plan}_{user_id}_{random.randint(1000000,9999999)}.jpg"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(image_bytes)
    
    image_url = f"/static/outputs/{filename}"
    dna = random.randint(1000000, 9999999)
    
    c.execute("INSERT INTO ascensions (user_id, plan, burden, dna, image_url) VALUES (?, ?, ?, ?, ?)",
              (user_id, plan, burden, dna, image_url))
    c.execute("UPDATE users SET total_ascensions = total_ascensions + 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    try:
        photo_file = BufferedInputFile(image_bytes, filename="ascension.jpg")
        await bot.send_photo(
            chat_id=user_id,
            photo=photo_file,
            caption=f"🌌 <b>Your {plan.upper()} Ascension is complete!</b>\n\n"
                    f"Burden: {burden}\n"
                    f"DNA: <code>{dna}</code>\n\n"
                    f"The Void has claimed you forever.",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Failed to send photo to {user_id}: {e}")
    
    return image_url, dna

# --- پنل ادمین کامل و حرفه‌ای ---
class AdminStates(StatesGroup):
    waiting_user_id = State()
    waiting_plan = State()
    waiting_photo = State()
    waiting_broadcast = State()

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⚠️ The Void recognizes only its true Emperor.")
    
    # جمع‌آوری آمار کامل
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM ascensions")
    total_ascensions = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM ascensions WHERE plan != 'eternal'")
    paid_ascensions = c.fetchone()[0]
    
    c.execute("SELECT SUM(free_mints) FROM users")
    remaining_free = c.fetchone()[0] or 0
    
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT COUNT(*) FROM ascensions WHERE date(timestamp) = ?", (today,))
    today_ascensions = c.fetchone()[0]
    
    conn.close()
    
    stats_text = f"""
🔱 <b>Emperor's Void Control Panel</b> 🔱
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}

👥 <b>Users & Activity</b>
• Total Users: <code>{total_users:,}</code>
• Total Ascensions: <code>{total_ascensions:,}</code>
• Paid Ascensions: <code>{paid_ascensions:,}</code>
• Today's Ascensions: <code>{today_ascensions}</code>
• Remaining Free Mints: <code>{remaining_free}</code>

🛠 <b>System Controls</b>
    """.strip()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Refresh Stats", callback_data="admin_refresh")],
        [InlineKeyboardButton(text="👤 Manual Mint for User", callback_data="admin_mint_user")],
        [InlineKeyboardButton(text="🔄 Reset All Free Mints", callback_data="admin_reset_all")],
        [InlineKeyboardButton(text="📢 Broadcast Message", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="📜 Last 20 Ascensions", callback_data="admin_last_asc")],
        [InlineKeyboardButton(text="👥 Top 10 Active Users", callback_data="admin_top_users")]
    ])
    
    await message.answer(stats_text, parse_mode="HTML", reply_markup=kb)

@dp.callback_query(lambda c: c.data == "admin_refresh")
async def admin_refresh(callback: types.CallbackQuery):
    await cmd_admin(callback.message)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_mint_user")
async def admin_mint_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.answer("👤 Enter Telegram User ID:")
    await state.set_state(AdminStates.waiting_user_id)

@dp.message(AdminStates.waiting_user_id)
async def admin_get_user_id(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        target_id = int(message.text)
        await state.update_data(target_id=target_id)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Eternal", callback_data="plan_eternal")],
            [InlineKeyboardButton(text="Divine", callback_data="plan_divine")],
            [InlineKeyboardButton(text="Celestial", callback_data="plan_celestial")],
            [InlineKeyboardButton(text="Legendary", callback_data="plan_legendary")]
        ])
        await message.answer("Choose level:", reply_markup=kb)
        await state.set_state(AdminStates.waiting_plan)
    except:
        await message.answer("Invalid ID.")

@dp.callback_query(lambda c: c.data.startswith("plan_"))
async def admin_select_plan(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    plan = callback.data.replace("plan_", "").capitalize()
    await state.update_data(plan=plan)
    await callback.message.answer(f"{plan} selected.\nSend photo or /skip:")
    await state.set_state(AdminStates.waiting_photo)

@dp.message(AdminStates.waiting_photo)
async def admin_mint_execute(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    data = await state.get_data()
    target_id = data['target_id']
    plan = data['plan']
    photo_base64 = None
    
    if message.photo:
        file_id = message.photo[-1].file_id
        file = await bot.get_file(file_id)
        photo_bytes = await bot.download_file(file.file_path)
        photo_base64 = base64.b64encode(photo_bytes.read()).decode('utf-8')
    elif message.text and message.text.lower() == "/skip":
        photo_base64 = None
    else:
        return await message.answer("Send photo or /skip.")
    
    await manual_mint(target_id, plan, "Emperor's Gift", photo_base64)
    await message.answer(f"✅ {plan} granted to {target_id}!")
    await state.clear()

@dp.callback_query(lambda c: c.data == "admin_reset_all")
async def admin_reset_all(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    c.execute("UPDATE users SET free_mints = 3")
    conn.commit()
    conn.close()
    await callback.message.answer("🔄 All free mints reset!")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_broadcast")
async def admin_broadcast_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.answer("📢 Send message to broadcast to all users:")
    await state.set_state(AdminStates.waiting_broadcast)

@dp.message(AdminStates.waiting_broadcast)
async def admin_broadcast_send(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    c.execute("SELECT id FROM users")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    
    success = 0
    for uid in users:
        try:
            await message.forward(uid)
            success += 1
            await asyncio.sleep(0.05)
        except:
            pass
    
    await message.answer(f"📢 Broadcast sent to {success}/{len(users)} users.")
    await state.clear()

@dp.callback_query(lambda c: c.data == "admin_last_asc")
async def admin_last_asc(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    c.execute("SELECT user_id, plan, burden, dna, timestamp FROM ascensions ORDER BY timestamp DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        return await callback.message.answer("No ascensions yet.")
    
    text = "📜 Last 20 Ascensions:\n\n"
    for row in rows:
        text += f"• {row[1]} | {row[2][:20]} | User_{str(row[0])[-4:]} | DNA: {row[3]} | {row[4][:16]}\n"
    
    await callback.message.answer(text)

@dp.callback_query(lambda c: c.data == "admin_top_users")
async def admin_top_users(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    c.execute("SELECT id, username, total_ascensions FROM users ORDER BY total_ascensions DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    
    text = "🏆 Top 10 Active Users:\n\n"
    for i, row in enumerate(rows, 1):
        text += f"{i}. {row[1] or 'User_'+str(row[0])[-4:]} — {row[2]} ascensions\n"
    
    await callback.message.answer(text)

# --- ثبت هندلرها ---
dp.message.register(cmd_start, CommandStart())
dp.message.register(cmd_admin, Command("admin"))

# --- FastAPI ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.delete_webhook(drop_pending_updates=True)
    webhook_url = "https://the-void-1.onrender.com/webhook"
    await bot.set_webhook(url=webhook_url)
    logger.info(f"Webhook set to {webhook_url}")
    yield
    await bot.delete_webhook()
    await bot.session.close()

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(path):
        return FileResponse(path)
    return "<h1>🌌 THE VOID</h1><p>index.html missing</p>"

@app.post("/webhook")
async def webhook(request: Request):
    try:
        update = types.Update(**await request.json())
        await dp.feed_update(bot=bot, update=update)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return {"ok": True}

@app.post("/api/mint")
async def api_mint(request: Request):
    try:
        data = await request.json()
        user_id = data.get('u')
        plan = data.get('plan', 'eternal').capitalize()
        burden = data.get('b', 'Unknown Burden')
        photo_base64 = data.get('p')
        
        if not user_id:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        
        conn = sqlite3.connect("void_data.db")
        c = conn.cursor()
        c.execute("SELECT free_mints FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()
        
        if plan == 'Eternal' and (not row or row[0] <= 0):
            conn.close()
            return JSONResponse({"error": "No free mints left"}, status_code=403)
        
        if plan == 'Eternal' and row and row[0] > 0:
            c.execute("UPDATE users SET free_mints = free_mints - 1 WHERE id = ?", (user_id,))
            conn.commit()
        
        conn.close()
        
        image_url, dna = await manual_mint(user_id, plan, burden, photo_base64)
        return JSONResponse({
            "status": "success",
            "message": "Ascension complete!",
            "image_url": image_url,
            "dna": dna
        })
    except Exception as e:
        logger.error(f"Mint error: {e}")
        return JSONResponse({"error": "The Void is restless."}, status_code=500)

@app.get("/api/gallery/{user_id}")
async def get_gallery(user_id: int):
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    c.execute("SELECT image_url, plan, dna, burden FROM ascensions WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
    items = [{"image": row[0], "plan": row[1], "dna": row[2], "burden": row[3]} for row in c.fetchall()]
    conn.close()
    return JSONResponse(items)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
