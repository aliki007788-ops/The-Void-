import os, random, math
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

def create_certificate(user_id, burden, photo_path=None):
    w, h = 1000, 1414
    img = Image.new('RGB', (w, h), '#000814')
    draw = ImageDraw.Draw(img)
    gold = '#CDA434'

    # انتخاب تصادفی یکی از ۲۰ حالت
    styles = [
        'classic_ornate', 'cosmic_nebula', 'gothic_seal', 'minimal_glow',
        'floral_luxury', 'alchemy_symbols', 'starburst_center', 'victorian_frame',
        'occult_runes', 'eternal_flame', 'celestial_rings', 'baroque_gold',
        'zodiac_wheel', 'sacred_geometry', 'art_deco', 'egyptian_hiero',
        'celtic_knots', 'mandala_void', 'crystal_lattice', 'aurora_crown'
    ]
    style = random.choice(styles)

    # پس‌زمینه ستاره‌ها (مشترک)
    for _ in range(350):
        x = random.randint(0, w)
        y = random.randint(0, h)
        size = random.choice([1, 1, 2, 3])
        draw.ellipse((x, y, x + size, y + size), fill='#FFFFFF')

    # اعمال افکت هر حالت
    if style == 'classic_ornate':
        draw.rectangle([40, 40, w-40, h-40], outline=gold, width=12)
        for cx, cy in [(40, 40), (w-40, 40), (40, h-40), (w-40, h-40)]:
            for r in [120, 80, 40]:
                draw.arc((cx - r, cy - r, cx + r, cy + r), start=0, end=90, fill=gold, width=8)

    elif style == 'cosmic_nebula':
        for i in range(h):
            r = int(30 + 40 * math.sin(i / h * math.pi))
            g = int(10 + 30 * math.cos(i / h * math.pi))
            b = int(60 + 60 * math.sin(i / h * 2 * math.pi))
            draw.line((0, i, w, i), fill=(r, g, b, 50))
        draw.rectangle([60, 60, w-60, h-60], outline=gold, width=10)

    elif style == 'gothic_seal':
        draw.rectangle([30, 30, w-30, h-30], outline=gold, width=18)
        draw.ellipse((w//2 - 140, h - 380, w//2 + 140, h - 80), outline=gold, width=12)
        draw.ellipse((w//2 - 80, h - 320, w//2 + 80, h - 140), fill=gold)

    elif style == 'minimal_glow':
        glow = Image.new('RGBA', (w+400, h+400), (0,0,0,0))
        dg = ImageDraw.Draw(glow)
        for i in range(400, 0, -25):
            alpha = int(70 * (i / 400))
            dg.ellipse((w//2 - i, h//2 - i, w//2 + i, h//2 + i), fill=(205,164,52,alpha))
        glow = glow.filter(ImageFilter.GaussianBlur(50))
        img.paste(glow, (-200, -200), glow)

    elif style == 'floral_luxury':
        for angle in range(0, 360, 20):
            rad = math.radians(angle)
            cx = w//2 + int(420 * math.cos(rad))
            cy = h//2 + int(620 * math.sin(rad))
            draw.ellipse((cx - 60, cy - 60, cx + 60, cy + 60), outline=gold, width=8)

    elif style == 'alchemy_symbols':
        symbols = ['△', '○', '□', '☆', '✦', '◉', '♄', '♃', '♁', '♆', '☿', '♀', '♂', '☉', '☽']
        for i in range(15):
            angle = i * 24
            rad = math.radians(angle)
            x = w//2 + int(380 * math.cos(rad))
            y = h//2 + int(380 * math.sin(rad))
            draw.text((x, y), random.choice(symbols), fill=gold, font=ImageFont.load_default())

    elif style == 'starburst_center':
        for i in range(80):
            angle = i * 4.5
            rad = math.radians(angle)
            length = 500
            x2 = w//2 + int(length * math.cos(rad))
            y2 = h//2 + int(length * math.sin(rad))
            draw.line((w//2, h//2, x2, y2), fill=gold, width=3)

    elif style == 'victorian_frame':
        draw.rectangle([50, 50, w-50, h-50], outline=gold, width=12)
        for cx, cy in [(50, 50), (w-50, 50), (50, h-50), (w-50, h-50)]:
            draw.polygon([(cx, cy), (cx+120, cy), (cx+60, cy+120)], fill=gold)

    elif style == 'occult_runes':
        runes = 'ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ'
        for _ in range(40):
            x = random.randint(100, w-100)
            y = random.randint(100, h-100)
            draw.text((x, y), random.choice(runes), fill=gold, font=ImageFont.load_default())

    elif style == 'eternal_flame':
        for _ in range(200):
            x = w//2 + random.randint(-300, 300)
            y = h//2 + random.randint(-400, 400)
            size = random.randint(8, 30)
            draw.ellipse((x, y, x+size, y+size), fill=(255, random.randint(120,180), 0))

    elif style == 'celestial_rings':
        for r in range(100, 500, 50):
            draw.ellipse((w//2 - r, h//2 - r, w//2 + r, h//2 + r), outline=gold, width=5)

    elif style == 'baroque_gold':
        draw.rectangle([30, 30, w-30, h-30], outline=gold, width=20)
        for cx, cy in [(30, 30), (w-30, 30), (30, h-30), (w-30, h-30)]:
            draw.arc((cx - 150, cy - 150, cx + 150, cy + 150), start=0, end=90, fill=gold, width=12)

    elif style == 'zodiac_wheel':
        for i in range(12):
            angle = i * 30
            rad = math.radians(angle)
            x = w//2 + int(400 * math.cos(rad))
            y = h//2 + int(400 * math.sin(rad))
            draw.ellipse((x - 40, y - 40, x + 40, y + 40), outline=gold, width=6)

    elif style == 'sacred_geometry':
        for level in range(6):
            r = 60 * (level + 1)
            for i in range(6):
                angle = i * 60
                rad = math.radians(angle)
                x = w//2 + int(r * math.cos(rad))
                y = h//2 + int(r * math.sin(rad))
                draw.ellipse((x - 30, y - 30, x + 30, y + 30), outline=gold, width=4)

    elif style == 'art_deco':
        for i in range(20):
            y = 100 + i * 60
            draw.line((100, y, w-100, y), fill=gold, width=4)
        draw.line((w//2, 100, w//2, h-100), fill=gold, width=8)

    elif style == 'egyptian_hiero':
        hiero = '𓀀𓀁𓀂𓀃𓀄𓀅𓀆𓀇𓀈𓀉'
        for _ in range(30):
            x = random.randint(100, w-100)
            y = random.randint(100, h-100)
            draw.text((x, y), random.choice(hiero), fill=gold, font=ImageFont.load_default())

    elif style == 'celtic_knots':
        for i in range(8):
            cx = 150 + i * 100
            for j in range(8):
                cy = 150 + j * 150
                draw.rectangle((cx, cy, cx+60, cy+60), outline=gold, width=6)

    elif style == 'mandala_void':
        for layer in range(10):
            r = 50 + layer * 40
            for i in range(36):
                angle = i * 10
                rad = math.radians(angle)
                x = w//2 + int(r * math.cos(rad))
                y = h//2 + int(r * math.sin(rad))
                draw.ellipse((x - 15, y - 15, x + 15, y + 15), fill=gold if layer % 2 == 0 else None, outline=gold, width=4)

    elif style == 'crystal_lattice':
        for i in range(-10, 11):
            for j in range(-10, 11):
                x = w//2 + i * 80
                y = h//2 + j * 80
                if random.random() > 0.3:
                    draw.ellipse((x - 30, y - 30, x + 30, y + 30), outline=gold, width=5)

    elif style == 'aurora_crown':
        for i in range(h):
            r = int(30 + 50 * math.sin(i / h * math.pi * 4))
            g = int(80 + 100 * math.sin(i / h * math.pi * 6))
            b = int(50 + 50 * math.cos(i / h * math.pi * 5))
            draw.line((0, i, w, i), fill=(r, g, b, 30))
        draw.ellipse((w//2 - 300, 50, w//2 + 300, 400), outline=gold, width=15)

    # لوگو V و عکس و متن‌ها (مشترک – از کد قبلی استفاده کن)

    path = f"nft_{user_id}_{style}.png"
    img.save(path)
    return path
