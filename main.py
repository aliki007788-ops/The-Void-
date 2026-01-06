import os
import random
import asyncio
import logging
import sqlite3
import requests
import base64
import cert_gen  # از cert_gen خودمان استفاده می‌کنیم
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
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
import uuid
import json

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- تنظیمات ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_API_TOKEN = os.getenv("HF_API_TOKEN", os.getenv("HF_TOKEN"))  # هر دو را بررسی می‌کنیم
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing!")

logger.info(f"HF Token available: {bool(HF_API_TOKEN)}")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-domain.com")
HF_MODEL = "runwayml/stable-diffusion-v1-5"  # هماهنگ با cert_gen

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
OUTPUT_DIR = os.path.join(STATIC_DIR, "outputs")
TEMP_DIR = os.path.join(STATIC_DIR, "temp")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# --- دیتابیس پیشرفته ---
def init_db():
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    
    # جدول کاربران
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY,
                 username TEXT,
                 ref_code TEXT UNIQUE,
                 ref_by INTEGER DEFAULT 0,
                 refs INTEGER DEFAULT 0,
                 free_mints INTEGER DEFAULT 3,
                 total_ascensions INTEGER DEFAULT 0,
                 stars_earned INTEGER DEFAULT 0,
                 stars_spent INTEGER DEFAULT 0,
                 created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                 last_active DATETIME DEFAULT CURRENT_TIMESTAMP
              )""")
    
    # جدول اسنشن‌ها (NFTها)
    c.execute("""CREATE TABLE IF NOT EXISTS ascensions (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 plan TEXT,
                 burden TEXT,
                 dna TEXT UNIQUE,
                 image_url TEXT,
                 style TEXT,
                 rarity TEXT,
                 stars_cost INTEGER DEFAULT 0,
                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                 FOREIGN KEY (user_id) REFERENCES users(id)
              )""")
    
    # جدول رفرال‌ها
    c.execute("""CREATE TABLE IF NOT EXISTS referrals (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 referrer_id INTEGER,
                 referred_id INTEGER UNIQUE,
                 status TEXT DEFAULT 'pending',
                 reward_given BOOLEAN DEFAULT 0,
                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                 FOREIGN KEY (referrer_id) REFERENCES users(id),
                 FOREIGN KEY (referred_id) REFERENCES users(id)
              )""")
    
    # جدول حراجی
    c.execute("""CREATE TABLE IF NOT EXISTS auctions (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 ascension_id INTEGER,
                 seller_id INTEGER,
                 starting_price INTEGER,
                 current_price INTEGER,
                 highest_bidder INTEGER,
                 status TEXT DEFAULT 'active',
                 end_time DATETIME,
                 created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                 FOREIGN KEY (ascension_id) REFERENCES ascensions(id),
                 FOREIGN KEY (seller_id) REFERENCES users(id)
              )""")
    
    # جدول پیشنهادها
    c.execute("""CREATE TABLE IF NOT EXISTS bids (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 auction_id INTEGER,
                 bidder_id INTEGER,
                 amount INTEGER,
                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                 FOREIGN KEY (auction_id) REFERENCES auctions(id),
                 FOREIGN KEY (bidder_id) REFERENCES users(id)
              )""")
    
    # جدول تراکنش‌های Stars
    c.execute("""CREATE TABLE IF NOT EXISTS transactions (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 amount INTEGER,
                 type TEXT, -- 'earn', 'spend', 'reward'
                 description TEXT,
                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                 FOREIGN KEY (user_id) REFERENCES users(id)
              )""")
    
    conn.commit()
    conn.close()

init_db()

# --- تابع‌های کمکی دیتابیس ---
def get_user(user_id):
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def update_user(user_id, **kwargs):
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    for key, value in kwargs.items():
        c.execute(f"UPDATE users SET {key} = ? WHERE id = ?", (value, user_id))
    conn.commit()
    conn.close()

def add_ascension(user_id, plan, burden, dna, image_url, style, stars_cost=0):
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO ascensions (user_id, plan, burden, dna, image_url, style, stars_cost) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, plan, burden, dna, image_url, style, stars_cost))
    
    c.execute("UPDATE users SET total_ascensions = total_ascensions + 1 WHERE id = ?", (user_id,))
    
    if stars_cost > 0:
        c.execute("UPDATE users SET stars_spent = stars_spent + ? WHERE id = ?", (stars_cost, user_id))
    
    conn.commit()
    conn.close()

# --- پیام خوش‌آمدگویی ---
WELCOME_MESSAGE = (
    "🌌 *Emperor of the Eternal Void, the cosmos summons you...*\n\n"
    "In the infinite depths of darkness, where stars have long faded and time itself has surrendered,\n"
    "*The Void* awaits your arrival — only the chosen few dare to ascend to immortality.\n\n"
    "Name your burden.\n"
    "Burn it in golden flames.\n"
    "And rise as the sovereign ruler of the eternal realm.\n\n"
    "Each ascension grants you a unique, forever-irreplaceable certificate — forged in celestial gold, "
    "sealed with the light of dead stars, bearing one of 30 rare imperial styles, and eternally tied to your soul.\n\n"
    "Only the boldest spirits step forward.\n"
    "*Are you one of them?*\n\n"
    "🔱 *Enter The Void now and claim your eternal crown.*\n\n"
    "This is not merely a journey.\n"
    "*This is the beginning of your everlasting reign.*\n\n"
    "_The Void bows to no one... except you._"
)

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    args = message.text.split()
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or "Unknown"
    
    # بررسی رفرال
    ref_by = None
    if len(args) > 1 and args[1].isdigit():
        ref_by = int(args[1])
    
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    
    # بررسی وجود کاربر
    c.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not c.fetchone():
        # ایجاد کاربر جدید
        ref_code = f"VOID{user_id:06d}"
        c.execute("""
            INSERT INTO users (id, username, ref_code, free_mints) 
            VALUES (?, ?, ?, ?)
        """, (user_id, username, ref_code, 3))
        
        # ثبت رفرال
        if ref_by and ref_by != user_id:
            c.execute("""
                INSERT INTO referrals (referrer_id, referred_id, status) 
                VALUES (?, ?, 'pending')
            """, (ref_by, user_id))
            
            # افزایش شمارش رفرال
            c.execute("UPDATE users SET refs = refs + 1 WHERE id = ?", (ref_by,))
            
            # بررسی پاداش (6 رفرال)
            c.execute("SELECT refs FROM users WHERE id = ?", (ref_by,))
            ref_count = c.fetchone()[0]
            if ref_count >= 6:
                # اعطای پاداش
                c.execute("UPDATE users SET free_mints = free_mints + 1 WHERE id = ?", (ref_by,))
                c.execute("UPDATE referrals SET reward_given = 1 WHERE referred_id = ?", (user_id,))
                
                # اطلاع‌رسانی به رفرر
                try:
                    await bot.send_message(
                        ref_by,
                        "🎉 *REFERAL BONUS UNLOCKED!*\n\n"
                        "You have reached 6 successful referrals!\n"
                        "A free ascension has been added to your account.",
                        parse_mode="Markdown"
                    )
                except:
                    pass
    
    conn.commit()
    conn.close()
    
    bot_username = (await bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    webapp_link = f"https://t.me/{bot_username}?startapp=void_{user_id}"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌌 ENTER THE VOID", web_app=WebAppInfo(url=f"{WEBAPP_URL}?startapp={user_id}"))],
        [InlineKeyboardButton(text="👥 Share Referral Link", url=f"https://t.me/share/url?url={ref_link}")],
        [InlineKeyboardButton(text="📱 Add to Story", url=f"https://t.me/share/url?url={webapp_link}&text=Join%20The%20Void")]
    ])
    
    full_msg = WELCOME_MESSAGE + f"\n\n🔗 *Your Referral Link:*\n`{ref_link}`\n\nInvite 6 worthy souls and your next ascension will be free."
    await message.answer(full_msg, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)

# --- تولید تصویر با استفاده از cert_gen ---
async def generate_certificate(user_id: int, plan: str, burden: str, photo_base64: str = None):
    try:
        # ذخیره عکس موقت
        photo_path = None
        if photo_base64:
            # حذق prefix
            if ',' in photo_base64:
                photo_base64 = photo_base64.split(',')[1]
            
            photo_filename = f"temp_{user_id}_{uuid.uuid4().hex[:8]}.png"
            photo_path = os.path.join(TEMP_DIR, photo_filename)
            
            with open(photo_path, 'wb') as f:
                f.write(base64.b64decode(photo_base64))
        
        # تبدیل plan به فرمت مورد نیاز cert_gen
        level_map = {
            'eternal': 'Eternal',
            'divine': 'Divine',
            'celestial': 'Celestial',
            'legendary': 'Legendary'
        }
        level = level_map.get(plan.lower(), 'Eternal')
        
        # فراخوانی cert_gen
        image_path, dna = cert_gen.create_certificate(
            user_id=user_id,
            burden=burden,
            photo_path=photo_path,
            level=level
        )
        
        # پاک کردن عکس موقت
        if photo_path and os.path.exists(photo_path):
            os.remove(photo_path)
        
        # تعیین rarity بر اساس level
        rarity_map = {
            'Eternal': 'Common',
            'Divine': 'Rare',
            'Celestial': 'Epic',
            'Legendary': 'Legendary'
        }
        rarity = rarity_map.get(level, 'Common')
        
        # تعیین هزینه Stars
        stars_cost_map = {
            'Eternal': 0,
            'Divine': 199,
            'Celestial': 299,
            'Legendary': 499
        }
        stars_cost = stars_cost_map.get(level, 0)
        
        # خواندن فایل تصویر برای ارسال به تلگرام
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        return image_bytes, dna, rarity, stars_cost
        
    except Exception as e:
        logger.error(f"Certificate generation error: {e}")
        raise

# --- تابع مینت اصلی بهبود یافته ---
async def process_mint(user_id: int, plan: str, burden: str, photo_base64: str = None):
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    
    # بررسی محدودیت روزانه برای Eternal
    if plan.lower() == 'eternal':
        c.execute("SELECT free_mints FROM users WHERE id = ?", (user_id,))
        free_mints = c.fetchone()[0]
        
        if free_mints <= 0:
            conn.close()
            return None, "❌ No free mints left today. Try a paid plan or wait until tomorrow."
        
        # کاهش تعداد مینت‌های رایگان
        c.execute("UPDATE users SET free_mints = free_mints - 1 WHERE id = ?", (user_id,))
    
    conn.commit()
    conn.close()
    
    try:
        # تولید گواهینامه
        image_bytes, dna, rarity, stars_cost = await generate_certificate(
            user_id, plan, burden, photo_base64
        )
        
        # ذخیره در دیتابیس
        filename = f"{plan}_{user_id}_{dna}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        
        image_url = f"/static/outputs/{filename}"
        
        # ذخیره اطلاعات اسنشن
        style = cert_gen.get_random_style(plan)  # فرض کنید تابعی داریم
        add_ascension(user_id, plan, burden, dna, image_url, style, stars_cost)
        
        # ارسال به کاربر
        photo_file = BufferedInputFile(image_bytes, filename="ascension_certificate.png")
        
        caption = f"""
🌌 *{plan.upper()} ASCENSION COMPLETE!*

*Burden:* {burden}
*DNA Code:* `{dna}`
*Rarity:* {rarity}
*Level:* {plan}

The Void has accepted your sacrifice.
Your soul is now forever inscribed in the eternal realm.
        """.strip()
        
        # ارسال به تلگرام
        await bot.send_photo(
            chat_id=user_id,
            photo=photo_file,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # ارسال دکمه‌های اکشن
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🖼 View Full Size", url=f"{WEBAPP_URL}{image_url}")],
            [InlineKeyboardButton(text="🔨 Put on Auction", callback_data=f"auction_{dna}")],
            [InlineKeyboardButton(text="🏆 Hall of Fame", web_app=WebAppInfo(url=f"{WEBAPP_URL}/hall"))]
        ])
        
        await bot.send_message(
            user_id,
            "*What would you like to do with your certificate?*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb
        )
        
        return image_url, dna
        
    except Exception as e:
        logger.error(f"Mint processing error: {e}")
        return None, f"❌ The Void is restless: {str(e)}"

# --- وب‌هوک FastAPI ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # راه‌اندازی اولیه
    await bot.delete_webhook(drop_pending_updates=True)
    
    # تنظیم webhook
    webhook_url = f"{WEBAPP_URL}/webhook"
    await bot.set_webhook(url=webhook_url)
    logger.info(f"Webhook set to {webhook_url}")
    
    yield
    
    # تمیزکاری
    await bot.delete_webhook()
    await bot.session.close()

app = FastAPI(
    title="THE VOID - Ascension API",
    description="Eternal NFT Ascension Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def home():
    index_path = os.path.join(BASE_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>🌌 THE VOID</h1><p>Ascension Platform</p>")

@app.post("/webhook")
async def webhook(request: Request):
    try:
        update = types.Update(**await request.json())
        await dp.feed_update(bot=bot, update=update)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return {"ok": True}

# --- API Endpoints جدید و کامل ---
@app.post("/api/mint")
async def api_mint(request: Request):
    try:
        data = await request.json()
        user_id = data.get('u')
        plan = data.get('plan', 'eternal')
        burden = data.get('b', 'Unknown Burden')
        photo_base64 = data.get('p')
        
        if not user_id:
            return JSONResponse(
                {"error": "Unauthorized", "message": "User ID required"},
                status_code=401
            )
        
        # پردازش مینت
        image_url, dna = await process_mint(user_id, plan, burden, photo_base64)
        
        if not image_url:
            return JSONResponse(
                {"error": "Mint failed", "message": dna},
                status_code=400
            )
        
        return JSONResponse({
            "status": "success",
            "message": "Ascension complete!",
            "data": {
                "image_url": image_url,
                "dna": dna,
                "plan": plan,
                "burden": burden,
                "view_url": f"{WEBAPP_URL}{image_url}"
            }
        })
        
    except Exception as e:
        logger.error(f"API mint error: {e}")
        return JSONResponse(
            {"error": "Internal server error", "message": str(e)},
            status_code=500
        )

@app.get("/api/user/{user_id}")
async def get_user_profile(user_id: int):
    user = get_user(user_id)
    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)
    
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    
    # آمار کاربر
    c.execute("SELECT COUNT(*) FROM ascensions WHERE user_id = ?", (user_id,))
    total_asc = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id = ? AND status = 'completed'", (user_id,))
    completed_refs = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM auctions WHERE seller_id = ?", (user_id,))
    auctions_count = c.fetchone()[0]
    
    conn.close()
    
    return JSONResponse({
        "user_id": user[0],
        "username": user[1],
        "ref_code": user[2],
        "refs": user[5],
        "free_mints": user[6],
        "total_ascensions": user[7],
        "stars_balance": user[8] - user[9],
        "stats": {
            "total_ascensions": total_asc,
            "completed_referrals": completed_refs,
            "auctions": auctions_count
        }
    })

@app.get("/api/gallery/{user_id}")
async def get_user_gallery(user_id: int):
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    
    c.execute("""
        SELECT a.dna, a.plan, a.burden, a.image_url, a.style, a.rarity, a.timestamp,
               (SELECT COUNT(*) FROM auctions au WHERE au.ascension_id = a.id) as on_auction
        FROM ascensions a
        WHERE a.user_id = ?
        ORDER BY a.timestamp DESC
    """, (user_id,))
    
    items = []
    for row in c.fetchall():
        items.append({
            "dna": row[0],
            "plan": row[1],
            "burden": row[2],
            "image_url": row[3],
            "style": row[4],
            "rarity": row[5],
            "timestamp": row[6],
            "on_auction": bool(row[7])
        })
    
    conn.close()
    return JSONResponse(items)

@app.get("/api/hall-of-fame")
async def hall_of_fame(limit: int = 60):
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    
    # 10 مورد آخر
    c.execute("""
        SELECT a.dna, a.plan, a.burden, a.image_url, a.style, u.username, a.timestamp
        FROM ascensions a
        JOIN users u ON a.user_id = u.id
        ORDER BY a.timestamp DESC
        LIMIT 10
    """)
    latest = [dict(zip(['dna', 'plan', 'burden', 'image_url', 'style', 'username', 'timestamp'], row)) 
              for row in c.fetchall()]
    
    # 50 مورد برتر (بر اساس rarity)
    c.execute("""
        SELECT a.dna, a.plan, a.burden, a.image_url, a.style, u.username, a.timestamp,
               CASE a.plan 
                   WHEN 'Legendary' THEN 4
                   WHEN 'Celestial' THEN 3
                   WHEN 'Divine' THEN 2
                   ELSE 1
               END as rarity_score
        FROM ascensions a
        JOIN users u ON a.user_id = u.id
        ORDER BY rarity_score DESC, a.timestamp DESC
        LIMIT 50
    """)
    top = [dict(zip(['dna', 'plan', 'burden', 'image_url', 'style', 'username', 'timestamp', 'rarity_score'], row)) 
           for row in c.fetchall()]
    
    conn.close()
    
    return JSONResponse({
        "latest_10": latest,
        "top_50": top
    })

@app.get("/api/auctions")
async def get_active_auctions():
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    
    c.execute("""
        SELECT 
            a.id as auction_id,
            ascn.dna,
            ascn.plan,
            ascn.burden,
            ascn.image_url,
            u.username as seller,
            a.current_price,
            a.starting_price,
            a.end_time,
            COUNT(b.id) as bid_count
        FROM auctions a
        JOIN ascensions ascn ON a.ascension_id = ascn.id
        JOIN users u ON a.seller_id = u.id
        LEFT JOIN bids b ON a.id = b.auction_id
        WHERE a.status = 'active'
        GROUP BY a.id
        ORDER BY a.end_time ASC
    """)
    
    auctions = []
    for row in c.fetchall():
        auctions.append({
            "auction_id": row[0],
            "dna": row[1],
            "plan": row[2],
            "burden": row[3],
            "image_url": row[4],
            "seller": row[5],
            "current_price": row[6],
            "starting_price": row[7],
            "end_time": row[8],
            "bid_count": row[9]
        })
    
    conn.close()
    return JSONResponse(auctions)

@app.get("/api/leaderboard")
async def get_leaderboard(type: str = "referrals"):
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    
    if type == "referrals":
        c.execute("""
            SELECT id, username, refs, total_ascensions
            FROM users 
            WHERE refs > 0
            ORDER BY refs DESC 
            LIMIT 10
        """)
        key = "refs"
    else:  # ascensions
        c.execute("""
            SELECT id, username, total_ascensions, refs
            FROM users 
            WHERE total_ascensions > 0
            ORDER BY total_ascensions DESC 
            LIMIT 10
        """)
        key = "total_ascensions"
    
    leaders = []
    for row in c.fetchall():
        leaders.append({
            "user_id": row[0],
            "username": row[1],
            "score": row[2],
            "other_stat": row[3]
        })
    
    conn.close()
    return JSONResponse({
        "type": type,
        "leaders": leaders
    })

# --- Admin API ---
@app.post("/api/admin/mint")
async def admin_mint(
    admin_key: str = Form(...),
    user_id: int = Form(...),
    plan: str = Form(...),
    burden: str = Form("Admin Gift"),
    photo: UploadFile = File(None)
):
    if admin_key != os.getenv("ADMIN_KEY", "void_master_2024"):
        return JSONResponse({"error": "Invalid admin key"}, status_code=403)
    
    photo_base64 = None
    if photo:
        photo_bytes = await photo.read()
        photo_base64 = base64.b64encode(photo_bytes).decode('utf-8')
    
    image_url, dna = await process_mint(user_id, plan, burden, photo_base64)
    
    if not image_url:
        return JSONResponse({"error": "Mint failed"}, status_code=400)
    
    return JSONResponse({
        "status": "success",
        "message": f"Admin mint completed for user {user_id}",
        "dna": dna,
        "image_url": image_url
    })

@app.get("/api/admin/stats")
async def admin_stats(admin_key: str):
    if admin_key != os.getenv("ADMIN_KEY", "void_master_2024"):
        return JSONResponse({"error": "Invalid admin key"}, status_code=403)
    
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    
    # آمار کلی
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM ascensions")
    total_ascensions = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM ascensions WHERE plan != 'eternal'")
    paid_ascensions = c.fetchone()[0]
    
    c.execute("SELECT SUM(stars_cost) FROM ascensions WHERE stars_cost > 0")
    total_stars = c.fetchone()[0] or 0
    
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT COUNT(*) FROM ascensions WHERE date(timestamp) = ?", (today,))
    today_asc = c.fetchone()[0]
    
    conn.close()
    
    return JSONResponse({
        "total_users": total_users,
        "total_ascensions": total_ascensions,
        "paid_ascensions": paid_ascensions,
        "total_stars_revenue": total_stars,
        "today_ascensions": today_asc,
        "timestamp": datetime.now().isoformat()
    })

# --- Endpoint برای King's Luck ---
@app.post("/api/kings-luck")
async def kings_luck_mint(request: Request):
    try:
        data = await request.json()
        user_id = data.get('u')
        burden = data.get('b', 'King\'s Fortune')
        photo_base64 = data.get('p')
        
        if not user_id:
            return JSONResponse({"error": "User ID required"}, status_code=401)
        
        # انتخاب تصادفی پلن با وزن‌های مختلف
        plans = ['eternal', 'divine', 'celestial', 'legendary']
        weights = [0.4, 0.3, 0.2, 0.1]  # 40% شانس eternal، 30% divine، و...
        
        random_val = random.random()
        cumulative = 0
        selected_plan = 'eternal'
        
        for plan, weight in zip(plans, weights):
            cumulative += weight
            if random_val <= cumulative:
                selected_plan = plan
                break
        
        # پردازش مینت
        image_url, dna = await process_mint(user_id, selected_plan, burden, photo_base64)
        
        if not image_url:
            return JSONResponse({"error": "Mint failed"}, status_code=400)
        
        return JSONResponse({
            "status": "success",
            "message": f"King's Luck awarded {selected_plan.upper()} ascension!",
            "data": {
                "won_plan": selected_plan,
                "image_url": image_url,
                "dna": dna,
                "burden": burden
            }
        })
        
    except Exception as e:
        logger.error(f"Kings luck error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# --- هندلرهای callback برای دکمه‌ها ---
@dp.callback_query(lambda c: c.data.startswith("auction_"))
async def start_auction(callback: types.CallbackQuery):
    dna = callback.data.replace("auction_", "")
    user_id = callback.from_user.id
    
    conn = sqlite3.connect("void_data.db")
    c = conn.cursor()
    
    # یافتن اسنشن
    c.execute("SELECT id FROM ascensions WHERE dna = ? AND user_id = ?", (dna, user_id))
    asc_row = c.fetchone()
    
    if not asc_row:
        await callback.answer("❌ Certificate not found", show_alert=True)
        return
    
    ascension_id = asc_row[0]
    
    # بررسی وجود حراج فعال
    c.execute("SELECT id FROM auctions WHERE ascension_id = ? AND status = 'active'", (ascension_id,))
    if c.fetchone():
        await callback.answer("❌ Already on auction", show_alert=True)
        conn.close()
        return
    
    # ایجاد حراج
    starting_price = 100  # قیمت پایه
    end_time = (datetime.now().timestamp() + 86400)  # 24 ساعت
    
    c.execute("""
        INSERT INTO auctions (ascension_id, seller_id, starting_price, current_price, end_time)
        VALUES (?, ?, ?, ?, ?)
    """, (ascension_id, user_id, starting_price, starting_price, end_time))
    
    conn.commit()
    conn.close()
    
    await callback.answer("✅ Listed on auction for 24 hours!", show_alert=True)
    
    # ارسال پیام تأیید
    await callback.message.answer(
        f"✅ *Auction Started!*\n\n"
        f"DNA: `{dna}`\n"
        f"Starting Price: *{starting_price} Stars*\n"
        f"Duration: *24 hours*\n\n"
        f"Check your auction in the auction room.",
        parse_mode=ParseMode.MARKDOWN
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
