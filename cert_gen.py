import os, random
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

def create_certificate(user_id, burden, photo_path=None):
    width, height = 1000, 1000
    # پس‌زمینه آبی عمیق و کیهانی
    img = Image.new('RGB', (width, height), color='#000814')
    draw = ImageDraw.Draw(img)

    # پس‌زمینه Nebula (ایجاد گرادینت و ستاره‌ها)
    for i in range(height):
        alpha = int(30 * (1 - i / height))
        draw.line((0, i, width, i), fill=(10, 5, 40, alpha))
    
    for _ in range(400):
        x, y = random.randint(20, width-20), random.randint(20, height-20)
        size = random.choice([1, 1, 1, 2])
        draw.ellipse((x, y, x+size, y+size), fill='#FFFFFF')

    # حاشیه Ornate طلایی
    border_color = '#FFD700'
    draw.rectangle([35, 35, 965, 965], outline=border_color, width=12)

    # گوشه‌های دکوراتیو پیچیده
    for cx, cy, rot in [(35, 35, 0), (965, 35, 90), (35, 965, 270), (965, 965, 180)]:
        for r in [90, 70, 50]:
            draw.arc((cx - r, cy - r, cx + r, cy + r), start=rot, end=rot+90, fill=border_color, width=10)
        draw.line((cx, cy + 60, cx + 40, cy + 100), fill=border_color, width=8)
        draw.line((cx + 60, cy, cx + 100, cy + 40), fill=border_color, width=8)

    # لوگوی V با نمادهای Occult
    logo_size = 400 if not photo_path else 350
    logo = Image.new('RGBA', (logo_size, logo_size), (0,0,0,0))
    d_logo = ImageDraw.Draw(logo)
    
    symbols = ['△', '○', '☆', '◉', '✦']
    for i, r in enumerate(range(190, 40, -25)):
        d_logo.ellipse((logo_size//2 - r, logo_size//2 - r, logo_size//2 + r, logo_size//2 + r), outline=border_color, width=6)
        if i < len(symbols):
            try: sym_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
            except: sym_font = ImageFont.load_default()
            d_logo.text((logo_size//2 + r - 10, logo_size//2), symbols[i], fill=border_color, font=sym_font)

    try: font_v = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 250 if photo_path else 300)
    except: font_v = ImageFont.load_default()
    d_logo.text((logo_size//2, logo_size//2 + 40), "V", fill=border_color, font=font_v, anchor="mm")
    
    img.paste(logo, ((width - logo_size) // 2, 80), logo)

    # بخش تصویر کاربر با Glow بسیار قوی
    y_text_start = 650 if not photo_path else 750
    if photo_path and os.path.exists(photo_path):
        try:
            p_img = Image.open(photo_path).convert("RGBA").resize((220, 220))
            mask = Image.new('L', (220, 220), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 220, 220), fill=255)
            p_img.putalpha(mask)

            glow = Image.new('RGBA', (300, 300), (0,0,0,0))
            d_glow = ImageDraw.Draw(glow)
            for i in range(40, 0, -3):
                alpha = int(220 * (i/40))
                d_glow.ellipse((i, i, 300-i, 300-i), fill=(255,215,0,alpha))
            glow = glow.filter(ImageFilter.GaussianBlur(20))
            img.paste(glow, (350, 450), glow)
            img.paste(p_img, (390, 470), p_img)
            draw.ellipse((380, 460, 620, 700), outline=border_color, width=10)
        except: pass

    # متون نهایی طلایی و گوتیک
    try:
        f_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 75)
        f_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except: f_title = f_sub = ImageFont.load_default()

    draw.text((500, y_text_start - 100), "VOID ASCENSION", fill=border_color, font=f_title, anchor="mm")
    draw.text((500, y_text_start), "THIS DOCUMENT CERTIFIES THAT", fill=border_color, font=f_sub, anchor="mm")
    draw.text((500, y_text_start + 110), f"\"{burden.upper()}\"", fill="#FFFFFF", font=f_title, anchor="mm")
    draw.text((500, y_text_start + 230), "HAS BEEN CONSUMED BY THE VOID", fill=border_color, font=f_sub, anchor="mm")
    draw.text((500, 930), f"HOLDER ID: {user_id} | 2025.VO-ID", fill="#888888", font=f_sub, anchor="mm")

    path = f"nft_{user_id}.png"
    img.save(path)
    return path
