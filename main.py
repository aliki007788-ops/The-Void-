import os
import json
import base64
import tempfile
import random
import time
import re
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup,
    Update, FSInputFile, LabeledPrice, PreCheckoutQuery,
    SuccessfulPayment, Message, CallbackQuery
)

from cert_gen import create_certificate, sanitize_burden, validate_image
from dotenv import load_dotenv

load_dotenv()

# ========== CONFIG ==========
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(storage=MemoryStorage())
app = FastAPI(title="THE VOID - Eternal Ascension")

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("WEBHOOK_URL", "")

# CORS برای وب‌اپ
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== PRICES ==========
PRICES = {
    "divine": 150,
    "celestial": 299, 
    "legendary": 499,
    "kings_luck": 199
}

# ========== APP STATUS ==========
APP_STATUS = {
    "free_enabled": True,
    "paid_enabled": True,
    "luck_enabled": True,
    "hall_enabled": True,
    "referral_enabled": True,
    "market_enabled": True
}

# ========== DATABASE CLASS (کامل) ==========
class VoidDatabase:
    def __init__(self):
        self.data = {
            "users": {},           # user_id -> user_data
            "certificates": [],    # همه گواهی‌ها
            "market": [],          # آیتم‌های فروش
            "referrals": {},       # user_id -> referral_count
            "transactions": [],    # تاریخچه تراکنش‌ها
            "daily_stats": {},     # آمار روزانه
            "admin_logs": []       # لاگ ادمین
        }
        self.file = "void_database.json"
        self.load()
    
    def load(self):
        """بارگذاری دیتابیس"""
        try:
            if os.path.exists(self.file):
                with open(self.file, "r", encoding='utf-8') as f:
                    loaded = json.load(f)
                    # مهاجرت از نسخه قدیمی
                    if "users" in loaded:
                        self.data.update(loaded)
        except Exception as e:
            print(f"Error loading DB: {e}")
            # ایجاد فایل جدید
            self.save()
    
    def save(self):
        """ذخیره دیتابیس"""
        try:
            with open(self.file, "w", encoding='utf-8') as f:
                json.dump(self.data, f, default=str, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving DB: {e}")
    
    # === USER METHODS ===
    def get_user(self, user_id: int) -> Dict:
        """دریافت کاربر یا ایجاد جدید"""
        uid = str(user_id)
        if uid not in self.data["users"]:
            self.data["users"][uid] = {
                "id": user_id,
                "username": "",
                "first_name": "",
                "burdens": [],  # تاریخچه burdenها
                "certificates": [],  # ID گواهی‌های کاربر
                "free_tries": {"count": 0, "date": datetime.now().date().isoformat()},
                "referrals": [],  # کسانی که دعوت کرده
                "discount": 0,   # درصد تخفیف
                "balance": 0,    # موجودی ستاره
                "created_at": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat()
            }
            self.save()
        return self.data["users"][uid]
    
    def update_user(self, user_id: int, updates: Dict):
        """آپدیت کاربر"""
        uid = str(user_id)
        if uid in self.data["users"]:
            self.data["users"][uid].update(updates)
            self.data["users"][uid]["last_active"] = datetime.now().isoformat()
            self.save()
    
    def add_user_certificate(self, user_id: int, cert_id: int):
        """افزودن گواهی به کاربر"""
        user = self.get_user(user_id)
        if cert_id not in user["certificates"]:
            user["certificates"].append(cert_id)
            self.update_user(user_id, {"certificates": user["certificates"]})
    
    def check_free_tries(self, user_id: int) -> bool:
        """بررسی تلاش‌های رایگان روزانه"""
        user = self.get_user(user_id)
        today = datetime.now().date().isoformat()
        
        if user["free_tries"]["date"] != today:
            # ریست روزانه
            user["free_tries"] = {"count": 0, "date": today}
            self.update_user(user_id, {"free_tries": user["free_tries"]})
        
        if user["free_tries"]["count"] >= 3:
            return False
        
        # افزایش شمارنده
        user["free_tries"]["count"] += 1
        self.update_user(user_id, {"free_tries": user["free_tries"]})
        return True
    
    # === CERTIFICATE METHODS ===
    def add_certificate(self, cert_data: Dict) -> int:
        """افزودن گواهی جدید"""
        cert_id = len(self.data["certificates"])
        cert_data["id"] = cert_id
        cert_data["created_at"] = datetime.now().isoformat()
        cert_data["dna"] = cert_data.get("dna", "UNKNOWN")
        
        self.data["certificates"].append(cert_data)
        self.save()
        return cert_id
    
    def get_certificate(self, cert_id: int) -> Optional[Dict]:
        """دریافت گواهی با ID"""
        for cert in self.data["certificates"]:
            if cert.get("id") == cert_id:
                return cert
        return None
    
    def get_user_certificates(self, user_id: int) -> List[Dict]:
        """گواهی‌های یک کاربر"""
        user = self.get_user(user_id)
        user_certs = []
        for cert_id in user.get("certificates", []):
            cert = self.get_certificate(cert_id)
            if cert:
                user_certs.append(cert)
        return user_certs
    
    # === HALL OF FAME ===
    def add_to_hall(self, cert_data: Dict):
        """افزودن به تالار مشاهیر"""
        if not APP_STATUS["hall_enabled"]:
            return
        
        hall_entry = {
            "cert_id": cert_data["id"],
            "user_id": cert_data["user_id"],
            "burden": cert_data["burden"],
            "level": cert_data["level"],
            "style": cert_data.get("style", "Unknown"),
            "date": cert_data["created_at"],
            "image_url": f"/api/certificate/{cert_data['dna']}"
        }
        
        # فقط سطوح بالا به تالار می‌روند
        if cert_data["level"] in ["Celestial", "Legendary"]:
            # حداکثر ۵۰ entry در تالار
            if len(self.data.get("hall", [])) >= 50:
                self.data["hall"] = self.data["hall"][-49:]
            
            self.data.setdefault("hall", []).append(hall_entry)
            self.save()
    
    def get_hall(self, limit: int = 20) -> List[Dict]:
        """دریافت تالار مشاهیر"""
        hall = self.data.get("hall", [])
        return sorted(hall, key=lambda x: x.get("date", ""), reverse=True)[:limit]
    
    # === MARKETPLACE ===
    def list_on_market(self, cert_id: int, price: int, seller_id: int):
        """لیست کردن گواهی در بازار"""
        cert = self.get_certificate(cert_id)
        if not cert or cert.get("user_id") != seller_id:
            return False
        
        market_item = {
            "cert_id": cert_id,
            "seller_id": seller_id,
            "price": price,
            "listed_at": datetime.now().isoformat(),
            "sold": False,
            "buyer_id": None
        }
        
        self.data["market"].append(market_item)
        self.save()
        return True
    
    def get_market_items(self, include_sold: bool = False) -> List[Dict]:
        """دریافت آیتم‌های بازار"""
        items = self.data.get("market", [])
        if not include_sold:
            items = [item for item in items if not item.get("sold", False)]
        return items
    
    # === REFERRAL SYSTEM ===
    def add_referral(self, referrer_id: int, referred_id: int):
        """ثبت رفرال"""
        if referrer_id == referred_id:
            return False
        
        ref_key = str(referrer_id)
        current = self.data["referrals"].get(ref_key, 0)
        self.data["referrals"][ref_key] = current + 1
        self.save()
        
        # اضافه کردن به لیست referrals کاربر
        user = self.get_user(referrer_id)
        if referred_id not in user.get("referrals", []):
            user["referrals"].append(referred_id)
            self.update_user(referrer_id, {"referrals": user["referrals"]})
        
        # بررسی تخفیف ۵۰٪
        if self.data["referrals"][ref_key] >= 5:
            self.update_user(referrer_id, {"discount": 50})
        
        return True
    
    def get_referral_count(self, user_id: int) -> int:
        """تعداد رفرال‌های کاربر"""
        return self.data["referrals"].get(str(user_id), 0)
    
    # === STATISTICS ===
    def get_stats(self) -> Dict:
        """آمار کلی سیستم"""
        return {
            "total_users": len(self.data["users"]),
            "total_certificates": len(self.data["certificates"]),
            "total_market_items": len([i for i in self.data.get("market", []) if not i.get("sold", False)]),
            "total_referrals": sum(self.data["referrals"].values()),
            "free_tries_today": sum(
                u.get("free_tries", {}).get("count", 0) 
                for u in self.data["users"].values() 
                if u.get("free_tries", {}).get("date") == datetime.now().date().isoformat()
            )
        }

db = VoidDatabase()

# ========== RATE LIMITER ==========
class RateLimiter:
    def __init__(self):
        self.requests: Dict[str, List[float]] = {}
        self.lock = asyncio.Lock()
    
    async def check(self, user_id: int, limit: int = 10, period: int = 60) -> bool:
        """بررسی rate limit"""
        async with self.lock:
            now = time.time()
            key = f"user_{user_id}"
            
            if key not in self.requests:
                self.requests[key] = []
            
            # حذف درخواست‌های قدیمی
            self.requests[key] = [t for t in self.requests[key] if now - t < period]
            
            if len(self.requests[key]) >= limit:
                return False
            
            self.requests[key].append(now)
            return True

rate_limiter = RateLimiter()

# ========== HELPER FUNCTIONS ==========
async def process_photo_upload(photo_data: str) -> Optional[str]:
    """پردازش آپلود عکس"""
    try:
        if not photo_data or "base64" not in photo_data:
            return None
        
        # استخراج داده base64
        img_base64 = photo_data.split(",")[1]
        img_bytes = base64.b64decode(img_base64)
        
        # بررسی سایز (حداکثر 5MB)
        if len(img_bytes) > 5 * 1024 * 1024:
            return None
        
        # ذخیره موقت
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        
        temp_path = temp_dir / f"photo_{int(time.time())}_{random.randint(1000, 9999)}.jpg"
        
        with open(temp_path, "wb") as f:
            f.write(img_bytes)
        
        # اعتبارسنجی با Pillow
        if not validate_image(str(temp_path)):
            os.remove(temp_path)
            return None
        
        return str(temp_path)
        
    except Exception as e:
        print(f"Photo processing error: {e}")
        return None

async def cleanup_temp_files():
    """پاکسازی فایل‌های موقت قدیمی"""
    try:
        temp_dir = Path("temp_uploads")
        cert_dir = Path("temp_certs")
        
        for directory in [temp_dir, cert_dir]:
            if directory.exists():
                for file in directory.glob("*"):
                    try:
                        # حذف فایل‌های قدیمی‌تر از ۱ ساعت
                        if time.time() - file.stat().st_mtime > 3600:
                            file.unlink()
                    except:
                        pass
    except:
        pass

async def send_certificate_to_user(user_id: int, burden: str, level: str, photo_path: Optional[str] = None) -> bool:
    """ارسال گواهینامه به کاربر"""
    try:
        print(f"Creating certificate for user {user_id}, level {level}")
        
        # ایجاد گواهینامه
        cert_path, style = create_certificate(user_id, burden, level, photo_path)
        
        if not cert_path or not os.path.exists(cert_path):
            await bot.send_message(user_id, "🌌 The cosmic forge failed. Please try again.")
            return False
        
        # تولید DNA از مسیر فایل
        dna = os.path.basename(cert_path).replace("cert_", "").replace(".png", "").split("_")[-1]
        
        # ایجاد entry در دیتابیس
        cert_id = db.add_certificate({
            "user_id": user_id,
            "burden": burden,
            "level": level,
            "style": style,
            "dna": dna,
            "image_path": cert_path,
            "file_size": os.path.getsize(cert_path)
        })
        
        # افزودن به کاربر
        db.add_user_certificate(user_id, cert_id)
        
        # افزودن به تالار (برای سطوح بالا)
        if level in ["Celestial", "Legendary"]:
            db.add_to_hall(db.get_certificate(cert_id))
        
        # متن کپشن
        caption = (
            f"🔱 <b>ASCENSION COMPLETE</b>\n\n"
            f"\"{burden.upper()}\"\n\n"
            f"<b>Level: {level}</b>\n"
            f"<b>Style: {style}</b>\n\n"
            f"Your eternal masterpiece is now part of the Void.\n"
            f"Holder ID: <code>{user_id}</code>\n"
            f"DNA Code: <code>{dna}</code>\n\n"
            f"2025.VO-ID | THE ETERNAL ARCHIVE"
        )
        
        # ارسال گواهینامه
        await bot.send_document(
            user_id, 
            FSInputFile(cert_path),
            caption=caption,
            parse_mode="HTML"
        )
        
        # پاکسازی فایل‌های موقت در پس‌زمینه
        async def cleanup():
            try:
                await asyncio.sleep(10)  # ۱۰ ثانیه تأخیر
                if os.path.exists(cert_path):
                    os.remove(cert_path)
                if photo_path and os.path.exists(photo_path):
                    os.remove(photo_path)
            except:
                pass
        
        asyncio.create_task(cleanup())
        
        return True
        
    except Exception as e:
        print(f"Error in send_certificate_to_user: {str(e)}")
        await bot.send_message(user_id, "❌ An error occurred. Please contact support.")
        return False

# ========== BOT COMMANDS (کامل) ==========
@dp.message(Command("start"))
async def start_command(message: types.Message):
    """دستور /start کامل"""
    user = message.from_user
    
    # پردازش رفرال
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1][4:])
            if referrer_id != user.id:
                db.add_referral(referrer_id, user.id)
                
                # اطلاع به دعوت‌کننده
                try:
                    await bot.send_message(
                        referrer_id,
                        f"🌟 <b>NEW SOUL ENTERED THE VOID!</b>\n\n"
                        f"User @{user.username or user.id} entered through your link.\n"
                        f"Total referrals: {db.get_referral_count(referrer_id)}\n\n"
                        f"5 referrals → 50% eternal discount!",
                        parse_mode="HTML"
                    )
                except:
                    pass
        except:
            pass
    
    # دریافت اطلاعات کاربر
    user_data = db.get_user(user.id)
    if user.username:
        user_data["username"] = user.username
    if user.first_name:
        user_data["first_name"] = user.first_name
    db.update_user(user.id, user_data)
    
    # ایجاد پیام خوش‌آمد
    username = (await bot.get_me()).username
    referral_count = db.get_referral_count(user.id)
    discount = 50 if referral_count >= 5 else 0
    
    welcome = f"""
🌌 <b>WELCOME TO THE ETERNAL VOID, {user.first_name or 'SOUL'}!</b> 🌌

<i>"Where burdens become crowns, and souls become legends."</i>

🏆 <b>YOUR STATUS:</b>
• Referrals: {referral_count}/5
• Eternal Discount: {discount}%
• Free tries today: {3 - user_data['free_tries']['count']}/3

⚡ <b>ASCENSION PATHS:</b>
1️⃣ <b>FREE ETERNAL</b> (3 daily) - Send your burden as message
2️⃣ <b>DIVINE</b> (150 ⭐) - Royal portrait with your image
3️⃣ <b>CELESTIAL</b> (299 ⭐) - Cosmic masterpiece
4️⃣ <b>LEGENDARY</b> (499 ⭐) - Ultimate eternal artifact
5️⃣ <b>KING'S LUCK</b> (199 ⭐) - Mystery ascension!

🎲 <b>KING'S LUCK CHANCES:</b>
• Legendary: 1% 👑
• Celestial: 9% 🌟  
• Divine: 30% 💎
• Eternal: 60% ✨

🔗 <b>YOUR REFERRAL LINK:</b>
<code>https://t.me/{username}?start=ref_{user.id}</code>

🎁 <b>REFERRAL REWARDS:</b>
• 5 referrals → 50% discount FOREVER
• Each referral → +10 stars balance

🚀 <b>ENTER THE PORTAL TO BEGIN:</b>
    """
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔱 ENTER VOID PORTAL", 
                web_app=WebAppInfo(url=f"{WEBHOOK_URL}/static/index.html")
            )
        ],
        [
            InlineKeyboardButton(text="👑 HALL OF FAME", callback_data="view_hall"),
            InlineKeyboardButton(text="📊 MY STATS", callback_data="my_stats")
        ]
    ])
    
    await message.answer(welcome, reply_markup=kb, parse_mode="HTML")

@dp.message(Command("stats"))
async def stats_command(message: types.Message):
    """آمار کاربر"""
    user_data = db.get_user(message.from_user.id)
    user_certs = db.get_user_certificates(message.from_user.id)
    
    stats = f"""
📊 <b>YOUR VOID STATISTICS</b>

👤 <b>Account:</b>
• ID: <code>{message.from_user.id}</code>
• Joined: {user_data.get('created_at', 'Unknown').split('T')[0]}
• Last active: Just now

🏆 <b>Achievements:</b>
• Certificates: {len(user_certs)}
• Burdens carried: {len(user_data.get('burdens', []))}
• Referrals: {db.get_referral_count(message.from_user.id)}/5
• Discount: {user_data.get('discount', 0)}%
• Balance: {user_data.get('balance', 0)} ⭐

🎨 <b>Certificate Breakdown:</b>
{sum(1 for c in user_certs if c.get('level') == 'Eternal')} × Eternal
{sum(1 for c in user_certs if c.get('level') == 'Divine')} × Divine  
{sum(1 for c in user_certs if c.get('level') == 'Celestial')} × Celestial
{sum(1 for c in user_certs if c.get('level') == 'Legendary')} × Legendary

🔗 <b>Share your glory:</b>
<code>https://t.me/{(await bot.get_me()).username}?start=ref_{message.from_user.id}</code>
    """
    
    await message.answer(stats, parse_mode="HTML")

@dp.message(Command("hall"))
async def hall_command(message: types.Message):
    """دستور مشاهده تالار"""
    hall = db.get_hall(limit=10)
    
    if not hall:
        await message.answer("🌌 The Hall of Eternity is empty. Be the first to ascend!")
        return
    
    hall_text = "🏆 <b>HALL OF ETERNITY - TOP 10</b>\n\n"
    
    for i, entry in enumerate(hall, 1):
        user_id = entry.get('user_id', 'Unknown')
        burden = entry.get('burden', 'Unknown')[:20]
        level = entry.get('level', 'Unknown')
        date = entry.get('date', '').split('T')[0]
        
        emoji = "👑" if level == "Legendary" else "🌟" if level == "Celestial" else "💎"
        
        hall_text += f"{i}. {emoji} <b>{level}</b>\n"
        hall_text += f"   \"{burden}\"\n"
        hall_text += f"   👤 User_{str(user_id)[-4:]} | 📅 {date}\n\n"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔱 ENTER PORTAL", web_app=WebAppInfo(url=f"{WEBHOOK_URL}/static/index.html"))
    ]])
    
    await message.answer(hall_text, reply_markup=kb, parse_mode="HTML")

# ========== FREE MODE HANDLER ==========
@dp.message(F.text & ~F.text.startswith("/"))
async def free_mode_handler(message: types.Message):
    """پردازش burden رایگان"""
    if not APP_STATUS["free_enabled"]:
        await message.answer("🌌 Free ascensions are currently disabled by the Void Council.")
        return
    
    # Rate limiting
    if not await rate_limiter.check(message.from_user.id, limit=5, period=60):
        await message.answer("⏳ Please wait 1 minute before your next ascension.")
        return
    
    # بررسی تلاش‌های رایگان
    if not db.check_free_tries(message.from_user.id):
        await message.answer(
            "🌌 Your 3 daily free ascensions are complete.\n\n"
            "Enter the portal for:\n"
            "• Divine (150 ⭐) - Royal portrait\n"
            "• Celestial (299 ⭐) - Cosmic masterpiece\n"
            "• Legendary (499 ⭐) - Ultimate artifact\n"
            "• King's Luck (199 ⭐) - Mystery reward!"
        )
        return
    
    burden = message.text.strip()
    if not burden or len(burden) < 2:
        await message.answer("Please enter a meaningful burden (at least 2 characters).")
        return
    
    # Sanitize و ذخیره
    burden = sanitize_burden(burden)
    user_data = db.get_user(message.from_user.id)
    user_data["burdens"].append(burden[:50])
    db.update_user(message.from_user.id, {"burdens": user_data["burdens"]})
    
    # ایجاد گواهینامه
    await message.answer("🌀 <b>The Void is forging your eternal certificate...</b>", parse_mode="HTML")
    success = await send_certificate_to_user(message.from_user.id, burden, "Eternal")
    
    if success:
        remaining = 3 - db.get_user(message.from_user.id)["free_tries"]["count"]
        await message.answer(
            f"✨ <b>FREE ASCENSION COMPLETE!</b>\n\n"
            f"Remaining free tries today: {remaining}/3\n\n"
            f"Enter the portal for premium ascensions!",
            parse_mode="HTML"
        )
    else:
        # بازگرداندن try اگر خطا رخ داد
        user_data["free_tries"]["count"] = max(0, user_data["free_tries"]["count"] - 1)
        db.update_user(message.from_user.id, {"free_tries": user_data["free_tries"]})

# ========== ADMIN SYSTEM (کامل) ==========
@dp.message(Command("admin"))
async def admin_panel_command(message: types.Message):
    """پنل ادمین کامل"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Access denied. Only Void Lords may enter.")
        return
    
    stats = db.get_stats()
    status_text = "🟢 ON" if APP_STATUS["free_enabled"] else "🔴 OFF"
    
    admin_text = f"""
👑 <b>VOID ADMIN REALM</b>

📊 <b>System Statistics:</b>
• Total Users: {stats['total_users']}
• Total Certificates: {stats['total_certificates']}
• Market Items: {stats['total_market_items']}
• Total Referrals: {stats['total_referrals']}
• Free tries today: {stats['free_tries_today']}

⚙️ <b>System Status:</b>
• Free Mode: {status_text}
• Paid Mode: {'🟢 ON' if APP_STATUS['paid_enabled'] else '🔴 OFF'}
• King's Luck: {'🟢 ON' if APP_STATUS['luck_enabled'] else '🔴 OFF'}
• Hall of Fame: {'🟢 ON' if APP_STATUS['hall_enabled'] else '🔴 OFF'}
• Marketplace: {'🟢 ON' if APP_STATUS['market_enabled'] else '🔴 OFF'}

🛠️ <b>Quick Actions:</b>
    """
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Toggle Free", callback_data="admin_toggle_free"),
            InlineKeyboardButton(text="💰 Toggle Paid", callback_data="admin_toggle_paid")
        ],
        [
            InlineKeyboardButton(text="🎲 Toggle Luck", callback_data="admin_toggle_luck"),
            InlineKeyboardButton(text="🏆 Toggle Hall", callback_data="admin_toggle_hall")
        ],
        [
            InlineKeyboardButton(text="🛒 Toggle Market", callback_data="admin_toggle_market"),
            InlineKeyboardButton(text="📊 Full Stats", callback_data="admin_full_stats")
        ],
        [
            InlineKeyboardButton(text="👑 Gen Legendary", callback_data="admin_gen_legendary"),
            InlineKeyboardButton(text="🌟 Gen Celestial", callback_data="admin_gen_celestial")
        ],
        [
            InlineKeyboardButton(text="💎 Gen Divine", callback_data="admin_gen_divine"),
            InlineKeyboardButton(text="🌀 Gen Eternal", callback_data="admin_gen_eternal")
        ],
        [
            InlineKeyboardButton(text="🧹 Cleanup Files", callback_data="admin_cleanup"),
            InlineKeyboardButton(text="📝 View Logs", callback_data="admin_view_logs")
        ]
    ])
    
    await message.answer(admin_text, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data.startswith("admin_"))
async def admin_callback_handler(callback: CallbackQuery):
    """هندلر callback ادمین"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Access denied!")
        return
    
    action = callback.data.replace("admin_", "")
    
    if action.startswith("toggle_"):
        feature = action.replace("toggle_", "")
        if f"{feature}_enabled" in APP_STATUS:
            APP_STATUS[f"{feature}_enabled"] = not APP_STATUS[f"{feature}_enabled"]
            status = "ENABLED" if APP_STATUS[f"{feature}_enabled"] else "DISABLED"
            await callback.answer(f"✅ {feature.upper()} {status}")
            await admin_panel_command(callback.message)
    
    elif action.startswith("gen_"):
        level = action.replace("gen_", "").capitalize()
        if level == "Eternal":
            burden = "Admin Eternal Creation"
        elif level == "Divine":
            burden = "Admin Divine Creation"  
        elif level == "Celestial":
            burden = "Admin Celestial Creation"
        else:  # Legendary
            burden = "Admin Legendary Creation"
        
        await callback.answer(f"Creating {level}...")
        success = await send_certificate_to_user(callback.from_user.id, burden, level)
        
        if success:
            await callback.message.answer(f"✅ {level} certificate created successfully!")
        else:
            await callback.message.answer(f"❌ Failed to create {level} certificate.")
    
    elif action == "cleanup":
        await cleanup_temp_files()
        await callback.answer("✅ Temp files cleaned up!")
    
    elif action == "full_stats":
        stats = db.get_stats()
        full_stats = f"""
📈 <b>FULL SYSTEM STATISTICS</b>

👥 <b>Users:</b> {stats['total_users']}
🎨 <b>Certificates:</b> {stats['total_certificates']}
🛒 <b>Market Items:</b> {stats['total_market_items']}
🔗 <b>Referrals:</b> {stats['total_referrals']}
🌀 <b>Free tries today:</b> {stats['free_tries_today']}

💾 <b>Database Size:</b> {os.path.getsize('void_database.json') / 1024:.1f} KB
🕒 <b>Server Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        await callback.message.answer(full_stats, parse_mode="HTML")
        await callback.answer()
    
    elif action == "view_logs":
        logs = db.data.get("admin_logs", [])[-10:]
        if not logs:
            await callback.message.answer("No logs available.")
        else:
            log_text = "📝 <b>Recent Admin Logs</b>\n\n"
            for log in reversed(logs):
                log_text += f"• {log.get('action', 'Unknown')} - {log.get('timestamp', 'Unknown')}\n"
            await callback.message.answer(log_text, parse_mode="HTML")
        await callback.answer()

# ========== PAYMENT SYSTEM (کامل) ==========
@app.post("/create_stars_invoice")
async def create_invoice_endpoint(request: Request):
    """Endpoint ایجاد invoice برای وب‌اپ"""
    try:
        data = await request.json()
        user_id = data.get("u")
        burden = data.get("b", "Eternal Sovereign")
        item_type = data.get("type")
        photo_data = data.get("p")
        
        if not user_id or not item_type:
            return JSONResponse({"error": "Missing parameters"}, status_code=400)
        
        # Rate limiting
        if not await rate_limiter.check(user_id, limit=3, period=30):
            return JSONResponse({"error": "Too many requests. Please wait."}, status_code=429)
        
        # Sanitize burden
        burden = sanitize_burden(burden)
        
        # بررسی فعال بودن حالت پرداخت
        if not APP_STATUS["paid_enabled"] and item_type != "kings_luck":
            return JSONResponse({"error": "Paid ascensions are currently disabled."}, status_code=503)
        
        # ===== KING'S LUCK =====
        if item_type == "kings_luck":
            if not APP_STATUS["luck_enabled"]:
                return JSONResponse({"error": "King's Luck is currently disabled."}, status_code=503)
            
            # محاسبه شانس
            chance = random.random()
            if chance < 0.01:  # 1%
                level = "Legendary"
                result = "JACKPOT! 🎰 LEGENDARY"
            elif chance < 0.1:  # 9%
                level = "Celestial"  
                result = "AMAZING! 🌟 CELESTIAL"
            elif chance < 0.4:  # 30%
                level = "Divine"
                result = "GREAT! 💎 DIVINE"
            else:  # 60%
                level = "Eternal"
                result = "GOOD! ✨ ETERNAL"
            
            # پردازش عکس
            photo_path = await process_photo_upload(photo_data) if photo_data else None
            
            # ذخیره burden کاربر
            user_data = db.get_user(user_id)
            user_data["burdens"].append(burden[:50])
            db.update_user(user_id, {"burdens": user_data["burdens"]})
            
            # ایجاد گواهینامه بلافاصله
            success = await send_certificate_to_user(user_id, burden, level, photo_path)
            
            if success:
                return JSONResponse({
                    "free": True,
                    "level": level,
                    "result": result,
                    "message": f"You received: {level} certificate!"
                })
            else:
                return JSONResponse({"error": "Failed to create certificate"}, status_code=500)
        
        # ===== PAID ASCENSIONS =====
        # محاسبه قیمت با تخفیف
        base_price = PRICES.get(item_type, PRICES["divine"])
        referral_count = db.get_referral_count(user_id)
        discount = 50 if referral_count >= 5 else 0
        final_price = int(base_price * (100 - discount) / 100)
        
        # پردازش عکس
        photo_path = await process_photo_upload(photo_data) if photo_data else None
        
        # ذخیره موقت داده‌ها
        temp_data = {
            "user_id": user_id,
            "burden": burden,
            "type": item_type,
            "photo_path": photo_path,
            "timestamp": datetime.now().isoformat()
        }
        
        # ایجاد invoice در تلگرام
        try:
            provider_token = os.getenv("PROVIDER_TOKEN")
            if not provider_token:
                return JSONResponse({"error": "Payment system not configured"}, status_code=503)
            
            level_map = {
                "divine": "Divine",
                "celestial": "Celestial",
                "legendary": "Legendary"
            }
            level_name = level_map.get(item_type, "Ascension")
            
            invoice_url = await bot.create_invoice_link(
                title=f"VOID {level_name.upper()} ASCENSION",
                description=f"Eternal certificate: \"{burden[:30]}\"",
                payload=json.dumps(temp_data),
                provider_token=provider_token,
                currency="XTR",
                prices=[LabeledPrice(label=f"{level_name} Ascension", amount=final_price)]
            )
            
            return JSONResponse({
                "url": invoice_url,
                "price": final_price,
                "discount": discount,
                "level": level_name
            })
            
        except Exception as e:
            print(f"Invoice creation error: {e}")
            return JSONResponse({"error": "Payment gateway error"}, status_code=500)
        
    except Exception as e:
        print(f"Invoice endpoint error: {e}")
        return JSONResponse({"error": "Internal server error"}, status_code=500)

@dp.pre_checkout_query()
async def pre_checkout_handler(query: PreCheckoutQuery):
    """هندلر قبل از پرداخت"""
    await query.answer(ok=True)

@dp.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    """هندلر پرداخت موفق"""
    try:
        payload = json.loads(message.successful_payment.invoice_payload)
        
        user_id = payload.get("user_id")
        burden = payload.get("burden", "Eternal Sovereign")
        item_type = payload.get("type", "divine")
        photo_path = payload.get("photo_path")
        
        if not user_id:
            await message.answer("❌ Payment error: Invalid data.")
            return
        
        # تعیین سطح بر اساس نوع
        level_map = {
            "divine": "Divine",
            "celestial": "Celestial",
            "legendary": "Legendary"
        }
        level = level_map.get(item_type, "Divine")
        
        # اطلاع به کاربر
        await message.answer(f"🌀 <b>FORGING YOUR {level.upper()} ASCENSION...</b>", parse_mode="HTML")
        
        # ایجاد گواهینامه
        success = await send_certificate_to_user(user_id, burden, level, photo_path)
        
        if success:
            await message.answer(
                f"✨ <b>PAID ASCENSION COMPLETE!</b>\n\n"
                f"Your {level} masterpiece has been added to your eternal archive.\n\n"
                f"Share your glory in the Hall of Eternity!",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                "❌ <b>ASCENSION FAILED</b>\n\n"
                "The cosmic forge encountered an error.\n"
                "Please contact @void_support for assistance.",
                parse_mode="HTML"
            )
            
    except Exception as e:
        print(f"Payment handler error: {e}")
        await message.answer("❌ Error processing payment. Contact support.")

# ========== API ENDPOINTS (کامل برای وب‌اپ) ==========
@app.get("/api/hall-of-fame")
async def get_hall_api(limit: int = 20, page: int = 1):
    """API تالار مشاهیر"""
    try:
        hall = db.get_hall(limit=100)  # همه را بگیر
        start = (page - 1) * limit
        end = start + limit
        
        paginated = hall[start:end]
        
        # تبدیل به فرمت مناسب وب‌اپ
        formatted = []
        for entry in paginated:
            formatted.append({
                "id": entry.get("cert_id"),
                "user_id": entry.get("user_id"),
                "username": f"User_{str(entry.get('user_id', 0))[-4:]}",
                "burden": entry.get("burden", "Unknown"),
                "level": entry.get("level", "Unknown"),
                "style": entry.get("style", "Unknown"),
                "date": entry.get("date", "").split("T")[0],
                "image_url": entry.get("image_url", ""),
                "level_emoji": "👑" if entry.get("level") == "Legendary" else 
                              "🌟" if entry.get("level") == "Celestial" else 
                              "💎" if entry.get("level") == "Divine" else "✨"
            })
        
        return JSONResponse({
            "success": True,
            "page": page,
            "limit": limit,
            "total": len(hall),
            "total_pages": (len(hall) + limit - 1) // limit,
            "hall": formatted
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/api/user/{user_id}")
async def get_user_api(user_id: int):
    """API اطلاعات کاربر"""
    try:
        user_data = db.get_user(user_id)
        user_certs = db.get_user_certificates(user_id)
        referral_count = db.get_referral_count(user_id)
        
        response = {
            "success": True,
            "user": {
                "id": user_id,
                "username": user_data.get("username", ""),
                "referral_count": referral_count,
                "discount": 50 if referral_count >= 5 else 0,
                "free_tries": {
                    "used": user_data.get("free_tries", {}).get("count", 0),
                    "remaining": max(0, 3 - user_data.get("free_tries", {}).get("count", 0)),
                    "date": user_data.get("free_tries", {}).get("date", "")
                },
                "balance": user_data.get("balance", 0),
                "created_at": user_data.get("created_at", "").split("T")[0]
            },
            "certificates": {
                "total": len(user_certs),
                "breakdown": {
                    "eternal": sum(1 for c in user_certs if c.get("level") == "Eternal"),
                    "divine": sum(1 for c in user_certs if c.get("level") == "Divine"),
                    "celestial": sum(1 for c in user_certs if c.get("level") == "Celestial"),
                    "legendary": sum(1 for c in user_certs if c.get("level") == "Legendary")
                },
                "recent": [
                    {
                        "id": cert.get("id"),
                        "burden": cert.get("burden", "Unknown"),
                        "level": cert.get("level", "Unknown"),
                        "date": cert.get("created_at", "").split("T")[0],
                        "dna": cert.get("dna", "UNKNOWN")
                    }
                    for cert in user_certs[-5:]  # آخرین ۵ گواهی
                ]
            },
            "referral_link": f"https://t.me/{(await bot.get_me()).username}?start=ref_{user_id}"
        }
        
        return JSONResponse(response)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/api/marketplace")
async def get_marketplace_api(limit: int = 20, page: int = 1):
    """API بازار"""
    try:
        if not APP_STATUS["market_enabled"]:
            return JSONResponse({
                "success": True,
                "enabled": False,
                "message": "Marketplace is temporarily disabled."
            })
        
        items = db.get_market_items(include_sold=False)
        start = (page - 1) * limit
        end = start + limit
        
        paginated = items[start:end]
        
        formatted = []
        for item in paginated:
            cert = db.get_certificate(item.get("cert_id"))
            if cert:
                formatted.append({
                    "cert_id": item.get("cert_id"),
                    "seller_id": item.get("seller_id"),
                    "price": item.get("price", 0),
                    "listed_at": item.get("listed_at", "").split("T")[0],
                    "burden": cert.get("burden", "Unknown"),
                    "level": cert.get("level", "Unknown"),
                    "style": cert.get("style", "Unknown"),
                    "seller_name": f"User_{str(item.get('seller_id', 0))[-4:]}"
                })
        
        return JSONResponse({
            "success": True,
            "enabled": True,
            "page": page,
            "limit": limit,
            "total": len(items),
            "items": formatted
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.post("/api/marketplace/list")
async def list_on_marketplace_api(request: Request):
    """API لیست کردن گواهی در بازار"""
    try:
        if not APP_STATUS["market_enabled"]:
            return JSONResponse({"success": False, "error": "Marketplace disabled"}, status_code=503)
        
        data = await request.json()
        user_id = data.get("user_id")
        cert_id = data.get("cert_id")
        price = data.get("price")
        
        if not all([user_id, cert_id, price]):
            return JSONResponse({"success": False, "error": "Missing parameters"}, status_code=400)
        
        if price < 10 or price > 10000:
            return JSONResponse({"success": False, "error": "Invalid price (10-10000 ⭐)"}, status_code=400)
        
        # بررسی مالکیت گواهی
        cert = db.get_certificate(cert_id)
        if not cert or cert.get("user_id") != user_id:
            return JSONResponse({"success": False, "error": "Certificate not found or not owned"}, status_code=404)
        
        # لیست در بازار
        success = db.list_on_market(cert_id, price, user_id)
        
        if success:
            return JSONResponse({
                "success": True,
                "message": "Certificate listed on marketplace!",
                "item_id": len(db.data["market"]) - 1
            })
        else:
            return JSONResponse({"success": False, "error": "Failed to list"}, status_code=500)
            
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/api/certificate/{dna}")
async def get_certificate_image(dna: str):
    """API دریافت تصویر گواهی با DNA"""
    try:
        # جستجوی گواهی با DNA
        cert = None
        for c in db.data["certificates"]:
            if c.get("dna") == dna:
                cert = c
                break
        
        if not cert or not cert.get("image_path") or not os.path.exists(cert["image_path"]):
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        return FileResponse(cert["image_path"], media_type="image/png")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/status")
async def get_system_status():
    """API وضعیت سیستم"""
    stats = db.get_stats()
    
    return JSONResponse({
        "success": True,
        "status": "operational",
        "features": APP_STATUS,
        "statistics": stats,
        "server_time": datetime.now().isoformat(),
        "version": "1.0.0"
    })

# ========== HEALTH & ROOT ENDPOINTS ==========
@app.get("/")
async def root():
    """صفحه اصلی API"""
    return {
        "app": "THE VOID - Eternal Ascension",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "webapp": "/static/index.html",
            "api_docs": "Coming soon...",
            "health": "/health",
            "hall_of_fame": "/api/hall-of-fame",
            "marketplace": "/api/marketplace"
        },
        "message": "Enter the Void, where burdens become crowns."
    }

@app.get("/health")
async def health_check():
    """Health check برای Render"""
    try:
        # بررسی اتصال دیتابیس
        db.save()  # تست نوشتن
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "bot": "connected" if await bot.get_me() else "disconnected",
            "memory_usage_mb": os.sys.getsizeof(db.data) / 1024 / 1024
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ========== STATIC FILES ==========
# ایجاد پوشه static اگر وجود ندارد
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

# ========== WEBHOOK HANDLER ==========
@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Webhook اصلی تلگرام"""
    try:
        update_data = await request.json()
        update = Update.model_validate(update_data, context={"bot": bot})
        await dp.feed_update(bot, update)
        return {"ok": True}
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"ok": False, "error": str(e)}, 500

# ========== STARTUP & SHUTDOWN ==========
@app.on_event("startup")
async def startup_event():
    """رویداد شروع برنامه"""
    print("=" * 50)
    print("🌌 THE VOID - Eternal Ascension")
    print("=" * 50)
    
    # پاکسازی فایل‌های موقت قدیمی
    await cleanup_temp_files()
    
    # تنظیم webhook
    if WEBHOOK_URL:
        webhook_url = f"{WEBHOOK_URL}/webhook"
        try:
            await bot.set_webhook(webhook_url)
            print(f"✅ Webhook set to: {webhook_url}")
        except Exception as e:
            print(f"⚠️ Failed to set webhook: {e}")
            print("⚠️ Running in polling mode")
    else:
        print("⚠️ WEBHOOK_URL not set, using getUpdates")
    
    # ایجاد پوشه‌های لازم
    Path("temp_uploads").mkdir(exist_ok=True)
    Path("temp_certs").mkdir(exist_ok=True)
    
    # نمایش آمار
    stats = db.get_stats()
    print(f"📊 Loaded: {stats['total_users']} users, {stats['total_certificates']} certificates")
    print("✅ THE VOID is ready for ascension!")
    print("=" * 50)

@app.on_event("shutdown")
async def shutdown_event():
    """رویداد خاموشی برنامه"""
    print("🌌 THE VOID is shutting down...")
    
    # ذخیره دیتابیس
    db.save()
    
    # پاکسازی فایل‌های موقت
    await cleanup_temp_files()
    
    print("✅ Data saved. Goodbye!")
    print("=" * 50)

# ========== MAIN ENTRY POINT ==========
if __name__ == "__main__":
    import uvicorn
    
    # پورت از محیط یا پیش‌فرض
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 Starting server on port {port}...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
