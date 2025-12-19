import os, random, math
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

def create_certificate(user_id, burden, photo_path=None):
    w, h = 1000, 1414
    img = Image.new('RGB', (w, h), '#000814')
    draw = ImageDraw.Draw(img)
    gold = '#CDA434'

    # انتخاب تصادفی یکی از ۱۰ حالت
    style = random.choice([
        'classic_ornate', 'cosmic_nebula', 'gothic_seal', 'minimal_glow',
        'floral_luxury', 'alchemy_symbols', 'starburst_center', 'victorian_frame',
        'occult_runes', 'eternal_flame'
    ])

    # پس‌زمینه ستاره‌ها
    for _ in range(300):
        x = random.randint(0, w)
        y = random.randint(0, h)
        size = random.choice([1, 2])
        draw.ellipse((x, y, x + size, y + size), fill='#FFFFFF')

    # اعمال افکت هر حالت
    if style == 'classic_ornate':
        draw.rectangle([40, 40, w-40, h-40], outline=gold, width=12)
        for cx, cy in [(40, 40), (w-40, 40), (40, h-40), (w-40, h-40)]:
            for r in [120, 80, 40]:
                draw.arc((cx - r, cy - r, cx + r, cy + r), start=0, end=90, fill=gold, width=8)

    elif style == 'cosmic_nebula':
        for i in range(h):
            r = int(20 + 30 * math.sin(i / h * math.pi))
            g = int(10 + 20 * math.cos(i / h * math.pi))
            b = int(50 + 50 * math.sin(i / h * 2 * math.pi))
            draw.line((0, i, w, i), fill=(r, g, b))
        draw.rectangle([50, 50, w-50, h-50], outline=gold, width=8)

    elif style == 'gothic_seal':
        draw.rectangle([30, 30, w-30, h-30], outline=gold, width=15)
        draw.ellipse((w//2 - 120, h - 350, w//2 + 120, h - 50), outline=gold, width=12)
        draw.ellipse((w//2 - 70, h - 300, w//2 + 70, h - 100), fill=gold)

    elif style == 'minimal_glow':
        glow = Image.new('RGBA', (w+200, h+200), (0,0,0,0))
        dg = ImageDraw.Draw(glow)
        for i in range(300, 0, -20):
            alpha = int(60 * (i / 300))
            dg.ellipse((w//2 - i, h//2 - i, w//2 + i, h//2 + i), fill=(205,164,52,alpha))
        glow = glow.filter(ImageFilter.GaussianBlur(40))
        img.paste(glow, (-100, -100), glow)
        draw.rectangle([80, 80, w-80, h-80], outline=gold, width=4)

    elif style == 'floral_luxury':
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            cx = w//2 + int(400 * math.cos(rad))
            cy = h//2 + int(600 * math.sin(rad))
            draw.ellipse((cx - 50, cy - 50, cx + 50, cy + 50), outline=gold, width=6)

    elif style == 'alchemy_symbols':
        symbols = ['△', '○', '□', '☆', '✦', '◉', '♄', '♃', '♁', '♆']
        for i in range(10):
            angle = i * 36
            rad = math.radians(angle)
            x = w//2 + int(350 * math.cos(rad))
            y = h//2 + int(350 * math.sin(rad))
            draw.text((x, y), random.choice(symbols), fill=gold, font=ImageFont.load_default())

    elif style == 'starburst_center':
        for i in range(60):
            angle = i * 6
            rad = math.radians(angle)
            length = 450
            x2 = w//2 + int(length * math.cos(rad))
            y2 = h//2 + int(length * math.sin(rad))
            draw.line((w//2, h//2, x2, y2), fill=gold, width=4)

    elif style == 'victorian_frame':
        draw.rectangle([50, 50, w-50, h-50], outline=gold, width=10)
        for cx, cy in [(50, 50), (w-50, 50), (50, h-50), (w-50, h-50)]:
            draw.polygon([(cx, cy), (cx+100, cy), (cx+50, cy+100)], fill=gold)

    elif style == 'occult_runes':
        runes = 'ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ'
        for _ in range(25):
            x = random.randint(100, w-100)
            y = random.randint(100, h-100)
            draw.text((x, y), random.choice(runes), fill=gold, font=ImageFont.load_default())

    elif style == 'eternal_flame':
        for _ in range(150):
            x = w//2 + random.randint(-250, 250)
            y = h//2 + random.randint(-300, 300)
            size = random.randint(5, 25)
            draw.ellipse((x, y, x+size, y+size), fill=(255, random.randint(100,150), 0))

    # لوگو V و عکس و متن‌ها (مشترک)
    # ... (کد قبلی برای لوگو، عکس، متن‌ها رو اینجا بذار – همون که قبلاً داشتی)

    path = f"nft_{user_id}_{style}.png"
    img.save(path)
    return path
