import os, base64, tempfile, json
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import LabeledPrice, FSInputFile
from cert_gen import create_certificate

app = FastAPI()
bot = Bot(token="YOUR_BOT_TOKEN")
dp = Dispatcher()

# Simple JSON Database
DB_FILE = "void_db.json"
def load_db(): 
    if not os.path.exists(DB_FILE): return {"users": {}, "auctions": [], "hall": []}
    return json.load(open(DB_FILE))

def save_db(db): json.dump(db, open(DB_FILE, 'w'))

@app.post("/create_stars_invoice")
async def create_invoice(request: Request):
    data = await request.json()
    uid = str(data['u'])
    rank = data.get('rank', 'free')
    price = 30 if data.get('type') == 'luck' else (120 if rank == 'rare' else 299)
    
    if rank == 'free':
        db = load_db()
        count = db['users'].get(uid, {}).get('free_mints', 0)
        if count >= 3: return {"error": "Limit reached"}
        
        path = create_certificate(uid, data['b'], None, 'free')
        db['users'][uid] = db['users'].get(uid, {"free_mints": 0})
        db['users'][uid]['free_mints'] += 1
        db['hall'].insert(0, path)
        save_db(db)
        await bot.send_document(uid, FSInputFile(path))
        return {"free": True}

    # Invoice logic...
    link = await bot.create_invoice_link(
        title=f"VOID {rank.upper()}", description="Ascend now.",
        payload=f"{uid}:{data['b']}:{rank}", currency="XTR",
        prices=[LabeledPrice(label="Stars", amount=price)]
    )
    return {"url": link}

@app.get("/get_hall_of_fame")
async def get_hall():
    db = load_db()
    return {"images": db['hall'][:50]}

@app.post("/start_auction")
async def start_auction(request: Request):
    data = await request.json()
    db = load_db()
    db['auctions'].append(data)
    save_db(db)
    return {"ok": True}

app.mount("/static", StaticFiles(directory="static"))
