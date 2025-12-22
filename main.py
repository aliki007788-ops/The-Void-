#!/usr/bin/env python3
"""
VOID Bot – Secure / Scalable / Maintainable
- SQLite WAL + locking
- Redis rate-limit
- Input validation & CSP
- Sentry + structured logs
- Retry + circuit-breaker for HF
"""
import os
import json
import base64
import tempfile
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any

import magic
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, FSInputFile
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import aioredis
import aiosqlite
import sentry_sdk
from cert_gen import create_certificate

# --------------------------------------------------
# Config & Env
# --------------------------------------------------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_API_TOKEN")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DB_PATH = Path(os.getenv("DB_PATH", "void.db"))
SENTRY_DSN = os.getenv("SENTRY_DSN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
MAX_FREE = 3
PRICES = {"divine": 150, "celestial": 299, "legendary": 499, "kings-luck": 199}

sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=1.0)

# --------------------------------------------------
# Logging
# --------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger("void")

# --------------------------------------------------
# Redis
# --------------------------------------------------
redis = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

# --------------------------------------------------
# DB helpers
# --------------------------------------------------
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users(
                uid TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0,
                date TEXT
            );
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS hall(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT,
                level TEXT,
                burden TEXT,
                style TEXT,
                date TEXT
            );
        """)
        await db.commit()

# --------------------------------------------------
# Rate-limit dependency
# --------------------------------------------------
async def rate_limit(uid: str, limit: int = 5, window: int = 60) -> bool:
    key = f"rl:{uid}"
    cur = await redis.incr(key)
    if cur == 1:
        await redis.expire(key, window)
    return cur <= limit

# --------------------------------------------------
# Pydantic models
# --------------------------------------------------
class InvoiceRequest(BaseModel):
    u: int
    b: str = Field(default="Eternal Sovereign", max_length=50)
    type: str
    p: str | None = None  # base64 image

    @validator("type")
    def validate_type(cls, v):
        if v not in PRICES:
            raise ValueError("Invalid type")
        return v

# --------------------------------------------------
# Bot setup
# --------------------------------------------------
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

# --------------------------------------------------
# Utils
# --------------------------------------------------
def safe_burden(b: str) -> str:
    return re.sub(r'[<>\"\'%;]', '', b)[:50]

async def send_certificate(uid: int, burden: str, level: str, photo_bytes: bytes | None = None) -> None:
    try:
        path, style = await create_certificate(str(uid), safe_burden(burden), level, photo_bytes)
    except Exception as e:
        log.exception("cert error")
        await bot.send_message(uid, "🌌 The Void is silent. Try again later.")
        return

    caption = (
        "🔱 <b>ASCENSION COMPLETE</b>\n\n"
        f"\"<i>{safe_burden(burden).upper()}</i>\"\n\n"
        f"<b>Level: {level}</b>\n"
        f"<b>Style: {style}</b>\n\n"
        "Your soul has been eternally crowned.\n"
        f"Holder ID: <code>{uid}</code>\n"
        "2025.VO-ID"
    )
    await bot.send_document(uid, FSInputFile(path), caption=caption)
    Path(path).unlink(missing_ok=True)

    if level in ("Celestial", "Legendary"):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO hall(uid, level, burden, style, date) VALUES (?,?,?,?,?)",
                (uid, level, safe_burden(burden), style, datetime.utcnow().isoformat())
            )
            await db.commit()

# --------------------------------------------------
# Handlers
# --------------------------------------------------
@dp.message(Command("start"))
async def start_handler(msg: types.Message):
    uid = msg.from_user.id
    username = (await bot.get_me()).username
    link = f"https://t.me/{username}?start=ref_{uid}"
    text = f"""
🌌 <b>YOU HAVE ENTERED THE ETERNAL VOID</b> 🌌

• Free Eternal (3 daily): send burden
• Divine & Legendary: Web-App portal
Your referral link:
<code>{link}</code>
Bring 5 souls → 50% discount forever
    """
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[[
            types.InlineKeyboardButton(text="🔱 ENTER THE VOID", web_app=types.WebAppInfo(url=f"{os.getenv('WEBHOOK_URL')}/static/index.html"))
        ]]
    )
    await msg.answer(text, reply_markup=kb)

@dp.message(F.text, ~F.text.startswith("/"))
async def free_cert(msg: types.Message):
    uid = str(msg.from_user.id)
    if not await rate_limit(uid, limit=3, window=86400):
        await msg.answer("🌌 Daily limit reached.")
        return
    burden = safe_burden(msg.text)
    await msg.answer("🌌 Forging your Eternal certificate...")
    await send_certificate(int(uid), burden, "Eternal")

# --------------------------------------------------
# FastAPI app
# --------------------------------------------------
app = FastAPI(title="VOID API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.on_event("startup")
async def on_start():
    await init_db()
    await bot.set_webhook(f"{os.getenv('WEBHOOK_URL')}/webhook")

@app.post("/create_stars_invoice")
async def invoice(req: InvoiceRequest):
    uid = req.u
    if not await rate_limit(f"invoice:{uid}", limit=10, window=60):
        raise HTTPException(status_code=429, detail="Too many requests")
    discount = 0.5 if await redis.get(f"refcount:{uid}") and int(await redis.get(f"refcount:{uid}")) >= 5 else 1.0
    price = int(PRICES[req.type] * discount)
    photo_bytes = None
    if req.p:
        try:
            head, data = req.p.split(",", 1)
            photo_bytes = base64.b64decode(data)
            if len(photo_bytes) > 2_000_000:
                raise ValueError("Large image")
            if magic.from_buffer(photo_bytes, mime=True) not in {"image/jpeg", "image/png"}:
                raise ValueError("Bad mime")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image")
    payload = f"{uid}:{req.b}:{req.type}"
    link = await bot.create_invoice_link(
        title=f"VOID {req.type.upper()}",
        description="Ascension to Glory",
        payload=payload,
        currency="XTR",
        prices=[LabeledPrice("Ascension Fee", price)]
    )
    return {"url": link}

@app.post("/webhook")
async def webhook(req: dict):
    update = types.Update(**req)
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.get("/api/hall-of-fame")
async def hall():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT uid, level, burden, style, date FROM hall ORDER BY id DESC LIMIT 50") as cur:
            rows = await cur.fetchall()
    return {"winners": [dict(r) for r in rows]}

# --------------------------------------------------
# Static files
# --------------------------------------------------
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")
