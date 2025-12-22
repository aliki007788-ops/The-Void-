import os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

def create_certificate(user_id, burden, photo_path=None, rank='free'):
    # تنظیمات ابعاد و رنگ
    w, h = 1000, 1414
    bg_color = "#000000"
    gold = "#FFD700"
    
    img = Image.new('RGB', (w, h), bg_color)
    draw = ImageDraw.Draw(img)
    
    # رسم خطوط هندسی مقدس (Sacred Geometry) در پس‌زمینه
    for i in range(5):
        r = 200 + i*50
        draw.ellipse((w//2-r, h//2-r-200, w//2+r, h//2+r-200), outline="#1a1a1a", width=2)

    # پردازش تصویر کاربر
    y_offset = 350
    if photo_path and os.path.exists(photo_path):
        user_img = Image.open(photo_path).convert('RGB')
        user_img = ImageOps.fit(user_img, (400, 400))
        
        # ماسک دایره‌ای
        mask = Image.new('L', (400, 400), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 400, 400), fill=255)
        
        # افکت درخشش دور عکس برای رتبه‌های بالا
        if rank != 'free':
            glow = Image.new('RGBA', (460, 460), (0,0,0,0))
            ImageDraw.Draw(glow).ellipse((10, 10, 450, 450), outline=gold, width=10)
            glow = glow.filter(ImageFilter.GaussianBlur(15))
            img.paste(glow, (w//2-230, y_offset-30), glow)
            
        img.paste(user_img, (w//2-200, y_offset), mask)
        draw.ellipse((w//2-205, y_offset-5, w//2+205, y_offset+405), outline=gold, width=5)

    # متون
    try:
        font_title = ImageFont.truetype("arial.ttf", 80)
        font_text = ImageFont.truetype("arial.ttf", 40)
    except:
        font_title = font_text = ImageFont.load_default()

    draw.text((w//2, y_offset+500), burden.upper(), fill="white", font=font_title, anchor="mm")
    draw.text((w//2, y_offset+600), f"RANK: {rank.upper()}", fill=gold, font=font_text, anchor="mm")
    draw.text((w//2, h-100), f"VERIFIED BY THE VOID | ID: {user_id}", fill="#333", font=font_text, anchor="mm")

    output = f"void_{user_id}.png"
    img.save(output)
    return output
