import os, json
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, types
from aiogram.types import LabeledPrice, FSInputFile
from cert_gen import create_certificate

app = FastAPI()
bot = Bot(token=os.getenv("BOT_TOKEN"))

# Storage Mock
DATABASE = {
    "config": {"wallet": True, "canvas": True, "feed": True, "leader": True},
    "feed": ["A new soul has entered the Void..."],
    "leaders": [{"n": "Aral", "s": 1250}, {"n": "Void-Master", "s": 980}]
}

@app.get("/get_void_config")
async def get_cfg(): return DATABASE["config"]

@app.post("/update_void_config")
async def upd_cfg(request: Request):
    data = await request.json()
    DATABASE["config"].update(data)
    return {"ok": True}

@app.post("/add_feed")
async def add_feed(request: Request):
    data = await request.json()
    msg = f"Soul {data['u']} sacrificed their burden: {data['b']}"
    DATABASE["feed"].append(msg)
    return {"ok": True}

@app.get("/get_feed")
async def get_feed(): return {"last": DATABASE["feed"][-1]}

@app.post("/create_stars_invoice")
async def create_invoice(request: Request):
    data = await request.json()
    uid, rank, burden = str(data['u']), data['rank'], data['b']
    ai_params = data.get('ai_params')
    
    prices = {"eternal": 0, "divine": 99, "celestial": 299, "legendary": 499}
    price = prices.get(rank, 0)

    if price == 0:
        path = create_certificate(uid, burden, data.get('p'), rank, ai_params)
        await bot.send_document(uid, FSInputFile(path), caption="Your Void Identity is ready.")
        return {"free": True}

    link = await bot.create_invoice_link(
        title=f"VOID ASCENSION: {rank.upper()}",
        description=f"Sacrifice Ritual for {burden}",
        payload=f"{uid}:{burden}:{rank}:{json.dumps(ai_params)}",
        currency="XTR",
        prices=[LabeledPrice(label="Ascension Fee", amount=price)]
    )
    return {"url": link}

app.mount("/static", StaticFiles(directory="static"))
