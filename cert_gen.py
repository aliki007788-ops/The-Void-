import os, random, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def create_certificate(user_id, burden, photo_path=None):
    w, h = 1000, 1000
    img = Image.new('RGB', (w, h), '#000814')
    draw = ImageDraw.Draw(img)
    
    for _ in range(300):
        draw.point((random.randint(0,w), random.randint(0,h)), fill='white')
    
    gold = '#FFD700'
    draw.rectangle([40, 40, 960, 960], outline=gold, width=12)
    
    # رسم لوگو V و متون (خلاصه شده برای اجرا)
    try:
        f_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        f_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except:
        f_big = f_sm = ImageFont.load_default()

    draw.text((500, 300), "VOID ASCENSION", fill=gold, font=f_big, anchor="mm")
    draw.text((500, 500), f"\"{burden}\"", fill="white", font=f_big, anchor="mm")
    draw.text((500, 800), f"HOLDER ID: {user_id}", fill=gold, font=f_sm, anchor="mm")
    
    path = f"nft_{user_id}.png"
    img.save(path)
    return path
