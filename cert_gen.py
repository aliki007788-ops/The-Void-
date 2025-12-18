import os
from PIL import Image, ImageDraw, ImageFont, ImageOps

def create_certificate(user_id, burden, photo_path=None):
    # ایجاد بوم مشکی خالص
    img = Image.new('RGB', (1000, 1000), color='#000')
    draw = ImageDraw.Draw(img)
    
    # حاشیه طلایی دوتایی
    draw.rectangle([20, 20, 980, 980], outline='#FFD700', width=3)
    draw.rectangle([40, 40, 960, 960], outline='#FFD700', width=1)
    
    y_text_start = 400
    if photo_path and os.path.exists(photo_path):
        try:
            p_img = Image.open(photo_path).convert("RGBA").resize((280, 280))
            mask = Image.new('L', (280, 280), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 280, 280), fill=255)
            p_img.putalpha(mask)
            img.paste(p_img, (360, 80), p_img)
            # دایره طلایی دور عکس
            draw.ellipse((355, 75, 645, 365), outline='#FFD700', width=4)
            y_text_start = 480
        except: pass

    # بارگذاری فونت
    try:
        font_main = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    except:
        font_main = font_sub = ImageFont.load_default()

    draw.text((500, y_text_start), "VOID ASCENSION", fill="#FFD700", font=font_main, anchor="mm")
    draw.text((500, y_text_start+100), "THIS SACRIFICE IS REGISTERED", fill="#888", font=font_sub, anchor="mm")
    draw.text((500, y_text_start+180), f"\"{burden.upper()}\"", fill="#FFF", font=font_main, anchor="mm")
    draw.text((500, 900), f"HOLDER: {user_id} | 2025.VO-ID", fill="#333", font=font_sub, anchor="mm")

    path = f"nft_{user_id}.png"
    img.save(path)
    return path
