import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import os

# تنظیمات API هوش مصنوعی
API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
HEADERS = {"Authorization": "Bearer YOUR_HUGGINGFACE_TOKEN"}

def generate_royal_certificate(user_img_bytes, burden_text, level_name, holder_id):
    """
    تولید گواهینامه سلطنتی با ترکیب هوش مصنوعی و طراحی لایه‌ای
    """
    
    # ۱. فراخوانی هوش مصنوعی برای ساخت پس‌زمینه اختصاصی بر اساس لول
    style_prompts = {
        "kings-luck": "A mystical purple and gold imperial frame, ethereal nebula background, royal textures, 8k",
        "divine": "A celestial golden frame, divine light rays, white and gold obsidian textures, 8k",
        "celestial": "A cosmic stardust frame, deep space aesthetic, ancient star-maps, glowing borders, 8k",
        "legendary": "An ancient dragon-scale golden frame, burning embers, legendary artifact style, cinematic lighting, 8k"
    }
    
    prompt = style_prompts.get(level_name.lower(), style_prompts["divine"])
    
    print(f"Generating Background for: {level_name}...")
    response = requests.post(API_URL, headers=HEADERS, json={"inputs": prompt})
    
    if response.status_code == 200:
        bg_img = Image.open(io.BytesIO(response.content)).resize((1024, 1024))
    else:
        # در صورت خطا، یک پس‌زمینه پیش‌فرض لوکس ساخته می‌شود
        bg_img = Image.new('RGB', (1024, 1024), color='#0a0a0a')

    # ۲. پردازش عکس کاربر (تبدیل به دایره با درخشش طلایی)
    if user_img_bytes:
        user_img = Image.open(io.BytesIO(user_img_bytes)).convert("RGBA")
        user_img = ImageOps.fit(user_img, (420, 420), centering=(0.5, 0.5))
        
        # ساخت ماسک دایره‌ای
        mask = Image.new('L', (420, 420), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, 420, 420), fill=255)
        
        # چسباندن عکس کاربر در مرکز گواهینامه
        bg_img.paste(user_img, (302, 260), mask)

    # ۳. نگارش متون با فونت سلطنتی Cinzel
    draw = ImageDraw.Draw(bg_img)
    font_path = "Cinzel.ttf"
    
    try:
        title_font = ImageFont.truetype(font_path, 80)
        info_font = ImageFont.truetype(font_path, 45)
        id_font = ImageFont.truetype(font_path, 30)
    except:
        print("Warning: Cinzel.ttf not found, using default font.")
        title_font = info_font = id_font = ImageFont.load_default()

    # رسم متون (با سایه برای خوانایی بیشتر)
    def draw_text_with_shadow(draw, pos, text, font, fill_color):
        x, y = pos
        # سایه نرم
        draw.text((x+2, y+2), text, font=font, fill="#000000", anchor="mm")
        # متن اصلی
        draw.text((x, y), text, font=font, fill=fill_color, anchor="mm")

    draw_text_with_shadow(draw, (512, 120), "VOID ASCENSION", title_font, "#FFD700")
    draw_text_with_shadow(draw, (512, 730), f"BURDEN: {burden_text.upper()}", info_font, "#FFFFFF")
    draw_text_with_shadow(draw, (512, 810), f"RANK: {level_name.upper()}", info_font, "#FFD700")
    draw_text_with_shadow(draw, (512, 920), f"HOLDER ID: {holder_id}", id_font, "#555555")

    # ذخیره و بازگرداندن تصویر نهایی
    output = io.BytesIO()
    bg_img.save(output, format="PNG")
    return output.getvalue()
