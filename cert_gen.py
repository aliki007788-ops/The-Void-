import os
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

# ۸ سبک اولیه – بعداً به ۳۰ تا گسترش می‌دیم
styles_config = {
    'classic_ornate': {'color': '#CDA434', 'name': 'Classic Ornate'},
    'cosmic_nebula': {'color': '#7B66FF', 'name': 'Cosmic Nebula'},
    'gothic_seal': {'color': '#E5E4E2', 'name': 'Gothic Seal'},
    'imperial_throne': {'color': '#FFD700', 'name': 'Imperial Throne ⚜️'},
    'crown_eclipse': {'color': '#FF4500', 'name': 'Crown Eclipse 🌑'},
    'sovereign_flame': {'color': '#FF8C00', 'name': 'Sovereign Flame 🔥'},
    'emerald_dynasty': {'color': '#50C878', 'name': 'Emerald Dynasty'},
    'obsidian_void': {'color': '#FFFFFF', 'name': 'Obsidian Void'},
}

def apply_divine_filter(photo):
    """فیلتر سینمایی لوکس – چهره واقعی حفظ می‌شه، فقط سلطنتی‌تر می‌شه"""
    # افزایش کنتراست و روشنایی
    photo = ImageEnhance.Contrast(photo).enhance(1.3)
    photo = ImageEnhance.Brightness(photo).enhance(1.1)
    
    # تن طلایی ملایم
    overlay = Image.new('RGB', photo.size, '#FFD700')
    photo = Image.blend(photo, overlay, alpha=0.1)
    
    # شارپنس ملایم
    photo = photo.filter(ImageFilter.SHARPEN)
    
    return photo

def create_certificate(user_id, burden, photo_path=None):
    w, h = 1000, 1414
    
    # انتخاب سبک تصادفی
    style = random.choice(list(styles_config.values()))
    gold = style['color']
    
    # بوم اصلی با مشکی عمیق
    img = Image.new('RGB', (w, h), '#000814')
    draw = ImageDraw.Draw(img)

    # ستاره‌های پس‌زمینه متراکم
    for _ in range(800):
        x = random.randint(0, w)
        y = random.randint(0, h)
        size = random.choice([1, 2])
        draw.ellipse((x-size, y-size, x+size, y+size), fill=random.choice(['#FFFFFF', '#FFD700', '#AAAAFF']))

    # قاب‌های طلایی چندلایه
    draw.rectangle([30, 30, w-30, h-30], outline=gold, width=6)
    draw.rectangle([60, 60, w-60, h-60], outline=gold, width=4)
    draw.rectangle([90, 90, w-90, h-90], outline=gold, width=8)

    y_text_start = 700 if photo_path else 800

    if photo_path and os.path.exists(photo_path):
        try:
            photo = Image.open(photo_path).convert('RGB')
            photo = apply_divine_filter(photo)
            photo = ImageOps.fit(photo, (500, 500))
            
            # ماسک دایره‌ای برای پرتره
            mask = Image.new('L', (500, 500), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, 500, 500), fill=255)
            photo.putalpha(mask)
            
            # glow درخشان دور پرتره
            glow = Image.new('RGBA', (560, 560), (0,0,0,0))
            glow_draw = ImageDraw.Draw(glow)
            glow_draw.ellipse((0, 0, 560, 560), outline=gold, width=30)
            glow = glow.filter(ImageFilter.GaussianBlur(20))
            
            img.paste(glow, (w//2 - 280, 300), glow)
            img.paste(photo, (w//2 - 250, 330), photo)
            
            # حاشیه طلایی دور پرتره
            draw.ellipse((w//2 - 255, 325, w//2 + 255, 835), outline=gold, width=8)
        except Exception as e:
            print(f"Photo processing error: {e}")
            y_text_start = 800
    else:
        # نشان مرکزی بزرگ برای حالت رایگان
        draw.ellipse((w//2 - 200, 400, w//2 + 200, 800), outline=gold, width=12)
        try:
            big_font = ImageFont.truetype("arial.ttf", 200)
            draw.text((w//2, 600), "V", fill=gold, font=big_font, anchor="mm")
        except:
            draw.text((w//2, 600), "V", fill=gold, anchor="mm")

    # فونت‌ها (با fallback)
    try:
        f_title = ImageFont.truetype("arial.ttf", 80)
        f_burden = ImageFont.truetype("arial.ttf", 60)
        f_info = ImageFont.truetype("arial.ttf", 40)
    except:
        f_title = f_burden = f_info = ImageFont.load_default()

    # متون اصلی
    draw.text((w//2, 150), "VOID ASCENSION", fill=gold, font=f_title, anchor="mm")
    draw.text((w//2, y_text_start), f"“{burden.upper()}”", fill="#FFFFFF", font=f_burden, anchor="mm")
    draw.text((w//2, y_text_start + 100), "HAS BEEN CONSUMED BY THE ETERNAL VOID", fill=gold, font=f_info, anchor="mm")
    draw.text((w//2, h - 200), f"Style: {style['name']}", fill=gold, font=f_info, anchor="mm")
    draw.text((w//2, h - 130), f"Holder ID: {user_id} | 2025.VO-ID", fill="#888888", font=f_info, anchor="mm")

    # ذخیره
    path = f"cert_{user_id}_{random.randint(10000, 99999)}.png"
    img.save(path, "PNG", quality=95)
    return path, style['name']
