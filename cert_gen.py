import os, random, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

styles_config = {
    'common': {'color': '#E5E4E2', 'name': 'Vagabond Soul', 'glow': 0},
    'rare': {'color': '#CDA434', 'name': 'Imperial Sovereign', 'glow': 35},
    'legendary': {'color': '#00ffff', 'name': 'Divine Eternal', 'glow': 60}
}

def draw_sacred_geometry(draw, w, h, color):
    cx, cy = w // 2, h // 2
    for i in range(12):
        radius = 100 + i * 40
        draw.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), outline=color, width=1 if i%2 else 2)

def create_certificate(user_id, burden, photo_path=None, rank='common'):
    w, h = 1000, 1414
    style = styles_config.get(rank, styles_config['common'])
    main_color = style['color']
    
    # Background
    img = Image.new('RGB', (w, h), '#00050a')
    draw = ImageDraw.Draw(img)
    
    # Stars & Geometry
    for _ in range(500):
        draw.point((random.randint(0,w), random.randint(0,h)), fill=random.choice(['#fff', main_color]))
    draw_sacred_geometry(draw, w, h, main_color)

    y_cursor = 400
    if photo_path and os.path.exists(photo_path):
        photo = Image.open(photo_path).convert('RGB')
        photo = ImageOps.fit(photo, (400, 400))
        mask = Image.new('L', (400, 400), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 400, 400), fill=255)
        
        if rank != 'common':
            glow = Image.new('RGBA', (500, 500), (0,0,0,0))
            ImageDraw.Draw(glow).ellipse((50,50,450,450), outline=main_color, width=15)
            glow = glow.filter(ImageFilter.GaussianBlur(style['glow']))
            img.paste(glow, (w//2-250, y_cursor-50), glow)
            
        img.paste(photo, (w//2-200, y_cursor), mask)
        draw.ellipse((w//2-205, y_cursor-5, w//2+205, y_cursor+405), outline=main_color, width=8)
        y_cursor += 480
    else:
        y_cursor += 200

    # Texts
    try: font_large = ImageFont.truetype("arial.ttf", 80); font_sub = ImageFont.truetype("arial.ttf", 45)
    except: font_large = font_sub = ImageFont.load_default()

    draw.text((w//2, y_cursor), f"RANK: {rank.upper()}", fill=main_color, font=font_sub, anchor="mm")
    draw.text((w//2, y_cursor+100), burden.upper(), fill="#FFFFFF", font=font_large, anchor="mm")
    draw.text((w//2, h-150), f"ID: {user_id} | THE VOID 2025", fill="#444", font=font_sub, anchor="mm")

    path = f"cert_{user_id}_{random.randint(1000,9999)}.png"
    img.save(path, "PNG")
    return path, style['name']
