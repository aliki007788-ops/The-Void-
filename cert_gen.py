import os
import random
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

# ۳۰ سبک کامل جهانی (با رنگ و نام)
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
    # sacred geometry mandala در پس‌زمینه
    center_x, center_y = w // 2, h // 2
    for i in range(6):
        radius = 100 + i * 60
        draw.ellipse((center_x - radius, center_y - radius, center_x + radius, center_y + radius), outline=gold, width=2)
        for j in range(12):
            angle = math.radians(j * 30)
            x1 = center_x + radius * math.cos(angle)
            y1 = center_y + radius * math.sin(angle)
            x2 = center_x + (radius + 40) * math.cos(angle)
            y2 = center_y + (radius + 40) * math.sin(angle)
            draw.line((x1, y1, x2, y2), fill=gold, width=1)

def create_certificate(user_id, burden, photo_path=None):
    w, h = 1000, 1414
    style_id = random.randint(1, 30)
    style = styles_config[style_id]
    gold = style['color']

    img = Image.new('RGB', (w, h), '#000000')
    draw = ImageDraw.Draw(img)

    # پس‌زمینه کیهانی با گرادیان و ستاره
    for _ in range(1000):
        x = random.randint(0, w)
        y = random.randint(0, h)
        size = random.randint(1, 3)
        draw.ellipse((x-size, y-size, x+size, y+size), fill=random.choice(['#FFFFFF', '#FFD700', '#AAAAFF', '#FF69B4']))

    # sacred geometry
    draw_sacred_geometry(draw, w, h, gold)

    # قاب‌های چندلایه لوکس
    for i in range(5):
        offset = 30 + i * 20
        width = 6 - i
        draw.rectangle([offset, offset, w-offset, h-offset], outline=gold, width=width)

    y_text = 200

    if photo_path and os.path.exists(photo_path):
        try:
            photo = Image.open(photo_path).convert('RGBA')
            photo = ImageEnhance.Contrast(photo).enhance(1.2)
            photo = ImageEnhance.Brightness(photo).enhance(1.1)
            photo = ImageOps.fit(photo, (450, 450))

            # ماسک دایره‌ای
            mask = Image.new('L', (450, 450), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, 450, 450), fill=255)
            photo.putalpha(mask)

            # glow قوی دور عکس
            glow = Image.new('RGBA', (550, 550), (0,0,0,0))
            glow_draw = ImageDraw.Draw(glow)
            for r in range(50, 0, -10):
                glow_draw.ellipse((r, r, 550-r, 550-r), outline=gold, width=5)
            glow = glow.filter(ImageFilter.GaussianBlur(30))

            img.paste(glow, (w//2 - 275, 350), glow)
            img.paste(photo, (w//2 - 225, 400), photo)

            # حاشیه جواهرنشان دور عکس
            draw.ellipse((w//2 - 230, 395, w//2 + 230, 905), outline=gold, width=10)
            y_text = 950
        except Exception as e:
            print(e)
            y_text = 800
    else:
        y_text = 800

    # فونت‌ها
    try:
        title_font = ImageFont.truetype("arial.ttf", 80)
        burden_font = ImageFont.truetype("arial.ttf", 60)
        info_font = ImageFont.truetype("arial.ttf", 35)
    except:
        title_font = burden_font = info_font = ImageFont.load_default()

    # متون اصلی
    draw.text((w//2, y_text - 200), "VOID ASCENSION CERTIFICATE", fill=gold, font=title_font, anchor="mm")
    draw.text((w//2, y_text), f"“{burden.upper()}”", fill="#FFFFFF", font=burden_font, anchor="mm")
    draw.text((w//2, y_text + 100), "HAS BEEN CONSUMED BY THE ETERNAL VOID", fill=gold, font=info_font, anchor="mm")
    draw.text((w//2, h - 200), f"Style: {style['name']}", fill=gold, font=info_font, anchor="mm")
    draw.text((w//2, h - 140), f"Holder ID: {user_id}", fill=gold, font=info_font, anchor="mm")
    draw.text((w//2, h - 80), "Timestamp: 2025.VO-ID", fill="#888888", font=info_font, anchor="mm")

    path = f"void_cert_{user_id}_{random.randint(10000,99999)}.png"
    img.save(path, "PNG", quality=95)
    return path, style['name']
