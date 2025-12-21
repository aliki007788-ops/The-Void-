import os
import random
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

# ۳۰ سبک جهانی با رنگ و نام منحصربه‌فرد
styles_config = {
    1: {'color': '#CDA434', 'name': 'Classic Ornate'},
    2: {'color': '#7B66FF', 'name': 'Cosmic Nebula'},
    3: {'color': '#E5E4E2', 'name': 'Gothic Seal'},
    4: {'color': '#FFD700', 'name': 'Imperial Throne'},
    5: {'color': '#FF4500', 'name': 'Crown Eclipse'},
    6: {'color': '#FF8C00', 'name': 'Sovereign Flame'},
    7: {'color': '#50C878', 'name': 'Emerald Dynasty'},
    8: {'color': '#FFFFFF', 'name': 'Obsidian Void'},
    9: {'color': '#00B7EB', 'name': 'Sapphire Eternity'},
    10: {'color': '#E0115F', 'name': 'Ruby Dominion'},
    11: {'color': '#9966CC', 'name': 'Amethyst Mystery'},
    12: {'color': '#E5E4E2', 'name': 'Platinum Reign'},
    13: {'color': '#B9F2FF', 'name': 'Diamond Ascendancy'},
    14: {'color': '#353839', 'name': 'Onyx Shadow'},
    15: {'color': '#00FFEF', 'name': 'Aurora Crown'},
    16: {'color': '#FFA500', 'name': 'Solar Empire'},
    17: {'color': '#C0C0C0', 'name': 'Lunar Sovereign'},
    18: {'color': '#8A2BE2', 'name': 'Nebula Throne'},
    19: {'color': '#000000', 'name': 'Void Emperor'},
    20: {'color': '#00CED1', 'name': 'Celestial Guardian'},
    21: {'color': '#FF4500', 'name': 'Eternal Phoenix'},
    22: {'color': '#FFD700', 'name': 'Divine Oracle'},
    23: {'color': '#FF69B4', 'name': 'Sacred Mandala'},
    24: {'color': '#4B0082', 'name': 'Royal Eclipse'},
    25: {'color': '#D4AF37', 'name': 'Imperial Dragon'},
    26: {'color': '#FFC0CB', 'name': 'Cosmic Lotus'},
    27: {'color': '#FFD700', 'name': 'Golden Pharaoh'},
    28: {'color': '#DC143C', 'name': 'Eternal Samurai'},
    29: {'color': '#8B0000', 'name': 'Void Spartan'},
    30: {'color': '#4682B4', 'name': 'Celestial Knight'},
}

def draw_sacred_geometry(draw, w, h, gold):
    """رسم sacred geometry در پس‌زمینه"""
    cx, cy = w // 2, h // 2
    for i in range(8):
        radius = 80 + i * 50
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=gold, width=2)
        for j in range(16):
            angle = math.radians(j * 22.5 + i * 11.25)
            x1 = cx + radius * math.cos(angle)
            y1 = cy + radius * math.sin(angle)
            x2 = cx + (radius + 60) * math.cos(angle)
            y2 = cy + (radius + 60) * math.sin(angle)
            draw.line((x1, y1, x2, y2), fill=gold, width=1)

def apply_divine_filter(photo, gold_color):
    """فیلتر سینمایی لوکس – چهره واقعی حفظ می‌شه"""
    photo = ImageEnhance.Contrast(photo).enhance(1.3)
    photo = ImageEnhance.Brightness(photo).enhance(1.15)
    overlay = Image.new('RGB', photo.size, gold_color)
    photo = Image.blend(photo, overlay, alpha=0.12)
    photo = photo.filter(ImageFilter.SHARPEN)
    return photo

def create_certificate(user_id, burden, photo_path=None):
    w, h = 1000, 1414
    
    # انتخاب سبک تصادفی
    style_id = random.randint(1, 30)
    style = styles_config[style_id]
    gold = style['color']
    
    # بوم اصلی
    img = Image.new('RGB', (w, h), '#000814')
    draw = ImageDraw.Draw(img)

    # پس‌زمینه کیهانی
    for _ in range(1000):
        x = random.randint(0, w)
        y = random.randint(0, h)
        size = random.randint(1, 3)
        draw.ellipse((x-size, y-size, x+size, y+size), fill=random.choice(['#FFFFFF', gold, '#AAAAFF', '#FF69B4']))

    # sacred geometry
    draw_sacred_geometry(draw, w, h, gold)

    # قاب‌های طلایی چندلایه
    for i in range(6):
        offset = 20 + i * 25
        width = 8 - i
        draw.rectangle([offset, offset, w-offset, h-offset], outline=gold, width=width)

    y_text = 200

    if photo_path and os.path.exists(photo_path):
        try:
            photo = Image.open(photo_path).convert('RGB')
            photo = apply_divine_filter(photo, gold)
            photo = ImageOps.fit(photo, (450, 450))

            # ماسک دایره‌ای
            mask = Image.new('L', (450, 450), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, 450, 450), fill=255)
            photo.putalpha(mask)

            # glow بسیار قوی
            glow = Image.new('RGBA', (550, 550), (0,0,0,0))
            glow_draw = ImageDraw.Draw(glow)
            for r in range(60, 0, -10):
                glow_draw.ellipse((r, r, 550-r, 550-r), outline=gold, width=6)
            glow = glow.filter(ImageFilter.GaussianBlur(35))

            img.paste(glow, (w//2 - 275, 350), glow)
            img.paste(photo, (w//2 - 225, 400), photo)

            # حاشیه جواهرنشان
            draw.ellipse((w//2 - 230, 395, w//2 + 230, 905), outline=gold, width=12)
            y_text = 950
        except Exception as e:
            print(f"Photo error: {e}")
            y_text = 800
    else:
        y_text = 800

    # فونت‌ها
    try:
        title_font = ImageFont.truetype("arial.ttf", 85)
        burden_font = ImageFont.truetype("arial.ttf", 65)
        info_font = ImageFont.truetype("arial.ttf", 40)
    except:
        title_font = burden_font = info_font = ImageFont.load_default()

    # متون اصلی
    draw.text((w//2, y_text - 200), "VOID ASCENSION CERTIFICATE", fill=gold, font=title_font, anchor="mm")
    draw.text((w//2, y_text), f"“{burden.upper()}”", fill="#FFFFFF", font=burden_font, anchor="mm")
    draw.text((w//2, y_text + 100), "HAS BEEN CONSUMED BY THE ETERNAL VOID", fill=gold, font=info_font, anchor="mm")
    draw.text((w//2, h - 250), f"Style: {style['name']}", fill=gold, font=info_font, anchor="mm")
    draw.text((w//2, h - 180), f"Holder ID: {user_id}", fill=gold, font=info_font, anchor="mm")
    draw.text((w//2, h - 110), "Timestamp: 2025.VO-ID", fill="#888888", font=info_font, anchor="mm")

    # ذخیره
    path = f"void_cert_{user_id}_{random.randint(10000,99999)}.png"
    img.save(path, "PNG", quality=95)
    return path, style['name']
