import os, random
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

def create_certificate(user_id, burden, photo_path=None):
    w, h = 1000, 1000
    img = Image.new('RGB', (w, h), '#000814')
    draw = ImageDraw.Draw(img)

    # ستاره‌ها
    for _ in range(300):
        x, y = random.randint(0, w), random.randint(0, h)
        draw.ellipse((x, y, x+2, y+2), fill='#FFFFFF')

    gold = '#FFD700'
    draw.rectangle([40, 40, 960, 960], outline=gold, width=12)

    # لوگو V
    logo_size = 400 if not photo_path else 340
    logo = Image.new('RGBA', (logo_size, logo_size), (0,0,0,0))
    d = ImageDraw.Draw(logo)
    for r in range(180, 40, -30):
        d.ellipse((logo_size//2 - r, logo_size//2 - r, logo_size//2 + r, logo_size//2 + r), outline=gold, width=8)
    try:
        f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(logo_size * 0.8))
    except:
        f = ImageFont.load_default()
    d.text((logo_size//2, logo_size//2 + 50), "V", fill=gold, font=f, anchor="mm")
    img.paste(logo, ((w - logo_size)//2, 80), logo)

    y_text = 650 if not photo_path else 750
    if photo_path:
        try:
            p = Image.open(photo_path).convert("RGBA").resize((240, 240))
            mask = Image.new('L', (240, 240), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 240, 240), fill=255)
            p.putalpha(mask)
            glow = Image.new('RGBA', (320, 320), (0,0,0,0))
            dg = ImageDraw.Draw(glow)
            for i in range(40, 0, -3):
                dg.ellipse((i, i, 320-i, 320-i), fill=(255,215,0,int(200*(i/40))))
            glow = glow.filter(ImageFilter.GaussianBlur(20))
            img.paste(glow, (340, 450), glow)
            img.paste(p, (380, 470), p)
            draw.ellipse((370, 460, 630, 710), outline=gold, width=10)
        except: pass

    try:
        ft = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 75)
        fs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except:
        ft = fs = ImageFont.load_default()

    draw.text((500, y_text - 100), "VOID ASCENSION", fill=gold, font=ft, anchor="mm")
    draw.text((500, y_text), "THIS DOCUMENT CERTIFIES THAT", fill=gold, font=fs, anchor="mm")
    draw.text((500, y_text + 100), f"\"{burden.upper()}\"", fill="#FFFFFF", font=ft, anchor="mm")
    draw.text((500, y_text + 220), "HAS BEEN CONSUMED BY THE ETERNAL VOID", fill=gold, font=fs, anchor="mm")
    draw.text((500, 920), f"HOLDER ID: {user_id}", fill=gold, font=fs, anchor="mm")
    draw.text((500, 970), "TIMESTAMP: 2025.VO-ID", fill="#888", font=fs, anchor="mm")

    path = f"nft_{user_id}.png"
    img.save(path)
    return path
