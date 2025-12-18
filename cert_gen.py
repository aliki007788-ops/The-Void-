import os, random, math
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

def create_certificate(user_id, burden, photo_path=None):
    width, height = 1000, 1000
    img = Image.new('RGB', (width, height), color='#000814')
    draw = ImageDraw.Draw(img)

    # Cosmic Background
    for i in range(height):
        alpha = int(35 * (1 - i / height))
        draw.line((0, i, width, i), fill=(15, 10, 50, alpha))
    for _ in range(350):
        x, y = random.randint(10, 990), random.randint(10, 990)
        draw.ellipse((x, y, x+1, y+1), fill='#FFFFFF')

    gold = '#FFD700'
    draw.rectangle([30, 30, 970, 970], outline=gold, width=12)

    # Ornate Corners
    for cx, cy, rot in [(30, 30, 0), (970, 30, 90), (30, 970, 270), (970, 970, 180)]:
        for r in [100, 75, 50]:
            draw.arc((cx-r, cy-r, cx+r, cy+r), start=rot, end=rot+90, fill=gold, width=8)

    is_premium = True if photo_path else False
    y_text = 680 if is_premium else 560

    if is_premium:
        # Divine Glow & Photo
        p_img = Image.open(photo_path).convert("RGBA").resize((250, 250))
        mask = Image.new('L', (250, 250), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 250, 250), fill=255)
        p_img.putalpha(mask)
        
        glow = Image.new('RGBA', (320, 320), (0,0,0,0))
        for i in range(35, 0, -2):
            alpha = int(200 * (i/35))
            ImageDraw.Draw(glow).ellipse((i, i, 320-i, 320-i), fill=(255, 215, 0, alpha))
        glow = glow.filter(ImageFilter.GaussianBlur(15))
        img.paste(glow, (340, 365), glow)
        img.paste(p_img, (375, 400), p_img)
        draw.ellipse((370, 395, 630, 655), outline=gold, width=10)

    # Dynamic Texts
    title = "DIVINE ASCENSION" if is_premium else "VOID ASCENSION"
    grade = "PREMIUM GRADE" if is_premium else "ETERNAL GRADE"
    
    try:
        f_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 75)
        f_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)
    except: f_title = f_sub = ImageFont.load_default()

    draw.text((500, 220), "V", fill=gold, font=f_title, anchor="mm")
    draw.ellipse((420, 140, 580, 300), outline=gold, width=5)
    
    draw.text((500, y_text), title, fill=gold, font=f_title, anchor="mm")
    draw.text((500, y_text+130), f"\"{burden.upper()}\"", fill="#FFF", font=f_title, anchor="mm")
    draw.text((500, y_text+250), f"RANK: {grade}", fill=gold, font=f_sub, anchor="mm")
    draw.text((500, 940), f"HOLDER: {user_id} | 2025.VO-ID", fill="#555", font=f_sub, anchor="mm")

    path = f"nft_{user_id}.png"
    img.save(path)
    return path
