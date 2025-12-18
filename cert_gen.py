import os
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

def create_certificate(user_id, burden, photo_path=None):
    width, height = 1000, 1000
    img = Image.new('RGB', (width, height), color='#000000')
    draw = ImageDraw.Draw(img)

    # پس‌زمینه cosmic با ستاره‌های ریز
    for _ in range(250):
        x = (_ * 17) % width
        y = (_ * 23) % height
        size = 1 if _ % 3 == 0 else 2
        draw.ellipse((x, y, x + size, y + size), fill='#FFFFFF')

    # حاشیه ornate طلایی با گوشه‌های decorative (دقیقاً مثل نمونه اولیه)
    border_color = '#FFD700'
    draw.rectangle([40, 40, 960, 960], outline=border_color, width=10)

    # گوشه‌های فلورال/ornate
    corner_patterns = [
        (40, 40), (960, 40), (40, 960), (960, 960)
    ]
    for cx, cy in corner_patterns:
        # arcهای decorative
        for r in [80, 60, 40]:
            draw.arc((cx - r, cy - r, cx + r, cy + r), start=0, end=90, fill=border_color, width=8)
        # خطوط اضافی برای ornate بودن
        draw.line((cx, cy + 50, cx, cy + 100), fill=border_color, width=6)
        draw.line((cx + 50, cy, cx + 100, cy), fill=border_color, width=6)

    # لوگو V بزرگ و mystical وسط بالا (دقیقاً مثل نمونه اولیه)
    logo_size = 380 if not photo_path else 320
    logo = Image.new('RGBA', (logo_size, logo_size), (0,0,0,0))
    d_logo = ImageDraw.Draw(logo)

    # دایره‌های concentric با افکت
    for r, w in [(180, 8), (150, 6), (120, 5), (90, 4), (60, 3)]:
        d_logo.ellipse((logo_size//2 - r, logo_size//2 - r, logo_size//2 + r, logo_size//2 + r), outline=border_color, width=w)

    # حرف V طلایی با فونت bold
    try:
        font_v = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 280)
    except:
        font_v = ImageFont.load_default()
    d_logo.text((logo_size//2, logo_size//2 + 40), "V", fill=border_color, font=font_v, anchor="mm")

    # چسباندن لوگو
    logo_x = (width - logo_size) // 2
    logo_y = 60 if not photo_path else 100
    img.paste(logo, (logo_x, logo_y), logo)

    # عکس کاربر زیر لوگو (اختیاری – با glow و shadow طلایی)
    y_text_start = 520 if not photo_path else 700
    if photo_path and os.path.exists(photo_path):
        try:
            p_img = Image.open(photo_path).convert("RGBA").resize((240, 240))

            # ماسک دایره‌ای
            mask = Image.new('L', (240, 240), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 240, 240), fill=255)
            p_img.putalpha(mask)

            # Glow طلایی لوکس
            glow = Image.new('RGBA', (300, 300), (0,0,0,0))
            d_glow = ImageDraw.Draw(glow)
            for i in range(25, 0, -2):
                alpha = int(200 * (i/25))
                d_glow.ellipse((i, i, 300-i, 300-i), fill=(255,215,0,alpha))
            glow = glow.filter(ImageFilter.GaussianBlur(12))
            img.paste(glow, (350, 420), glow)

            # Shadow نرم
            shadow = Image.new('RGBA', (260, 260), (0,0,0,0))
            d_shadow = ImageDraw.Draw(shadow)
            d_shadow.ellipse((15, 15, 245, 245), fill=(0,0,0,140))
            shadow = shadow.filter(ImageFilter.GaussianBlur(18))
            img.paste(shadow, (370, 440), shadow)

            img.paste(p_img, (380, 430), p_img)

            # حاشیه طلایی دور عکس
            draw.ellipse((370, 425, 630, 685), outline=border_color, width=8)

        except Exception as e:
            print(f"Photo error: {e}")

    # متن‌ها با فونت gothic و طلایی (حس رسمی و ابدی)
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
    except:
        font_title = font_sub = font_small = ImageFont.load_default()

    draw.text((500, y_text_start - 80), "VOID ASCENSION", fill="#FFD700", font=font_title, anchor="mm")
    draw.text((500, y_text_start + 20), "THIS DOCUMENT CERTIFIES THAT", fill="#FFD700", font=font_sub, anchor="mm")
    draw.text((500, y_text_start + 120), f"\"{burden.upper()}\"", fill="#FFFFFF", font=font_title, anchor="mm")
    draw.text((500, y_text_start + 240), "HAS BEEN CONSUMED BY", fill="#FFD700", font=font_sub, anchor="mm")
    draw.text((500, y_text_start + 300), "THE ETERNAL VOID", fill="#FFD700", font=font_sub, anchor="mm")
    draw.text((500, 920), f"HOLDER ID: {user_id}", fill="#FFD700", font=font_small, anchor="mm")
    draw.text((500, 970), "TIMESTAMP: 2025.VO-ID", fill="#BBBBBB", font=font_small, anchor="mm")

    path = f"nft_{user_id}.png"
    img.save(path)
    return path
