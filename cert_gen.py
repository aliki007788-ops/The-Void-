import os
import random
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

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

def apply_royal_filter(user_img, accent_color):
    user_img = ImageOps.autocontrast(user_img, cutoff=2)
    overlay = Image.new('RGBA', user_img.size, accent_color)
    return Image.blend(user_img, overlay, alpha=0.15)

def create_certificate(user_id, burden, photo_path=None):
    w, h = 1000, 1414
    style_key = random.choice(list(styles_config.keys()))
    conf = styles_config.get(style_key, {'color': '#CDA434', 'name': 'Divine Void'})
    gold = conf['color']

    img = Image.new('RGB', (w, h), color='#00050A')
    draw = ImageDraw.Draw(img)

    for _ in range(600):
        x, y = random.randint(0, w), random.randint(0, h)
        draw.point((x, y), fill=random.choice(['#FFFFFF', gold, '#444444']))

    draw.rectangle([20, 20, w-20, h-20], outline=gold, width=2)
    draw.rectangle([40, 40, w-40, h-40], outline=gold, width=8)
    
    if photo_path:
        try:
            p = Image.open(photo_path).convert("RGBA")
            p = apply_royal_filter(p, gold)
            p = ImageOps.fit(p, (400, 400), centering=(0.5, 0.5))
            
            mask = Image.new('L', (400, 400), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 400, 400), fill=255)
            p.putalpha(mask)

            glow = Image.new('RGBA', (460, 460), (0,0,0,0))
            ImageDraw.Draw(glow).ellipse((0, 0, 460, 460), outline=gold, width=20)
            glow = glow.filter(ImageFilter.GaussianBlur(15))
            
            img.paste(glow, (w//2 - 230, 320), glow)
            img.paste(p, (w//2 - 200, 350), p)
            draw.ellipse((w//2 - 205, 345, w//2 + 205, 755), outline=gold, width=5)
            y_text_start = 850
        except:
            y_text_start = 700
    else:
        y_text_start = 700

    try:
        f_title = ImageFont.truetype("fonts/Cinzel-Bold.ttf", 70)
        f_burden = ImageFont.truetype("fonts/Cinzel-Regular.ttf", 60)
        f_footer = ImageFont.truetype("fonts/Cinzel-Regular.ttf", 30)
    except:
        f_title = f_burden = f_footer = ImageFont.load_default()

    draw.text((w//2, 200), "VOID ASCENSION", fill=gold, font=f_title, anchor="mm")
    draw.text((w//2, y_text_start), f"“{burden.upper()}”", fill="#FFFFFF", font=f_burden, anchor="mm")
    
    draw.line((300, y_text_start + 80, 700, y_text_start + 80), fill=gold, width=2)
    
    draw.text((w//2, y_text_start + 150), "ETERNALLY ENSHRINED IN THE VOID", fill=gold, font=f_footer, anchor="mm")
    draw.text((w//2, h - 150), f"STYLE: {conf['name']} | HOLDER: {user_id}", fill=gold, font=f_footer, anchor="mm")
    draw.text((w//2, h - 100), "ERA: 2025.VO-ID", fill="#555555", font=f_footer, anchor="mm")

    path = f"nft_{user_id}_{random.randint(1000,9999)}.png"
    img.save(path, "PNG", quality=95)
    return path, conf['name']
