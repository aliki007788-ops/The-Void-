import os
from PIL import Image, ImageDraw, ImageFont

def create_certificate(user_id, burden):
    width, height = 1000, 1000
    image = Image.new('RGB', (width, height), color='#000000')
    draw = ImageDraw.Draw(image)

    # طراحی حاشیه طلایی دوتایی
    draw.rectangle([20, 20, 980, 980], outline='#FFD700', width=3)
    draw.rectangle([45, 45, 955, 955], outline='#FFD700', width=1)

    # تلاش برای بارگذاری فونت سیستم یا پیش‌فرض
    try:
        # در اکثر سرورهای لینوکس این مسیر وجود دارد
        font_main = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 65)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 35)
    except:
        font_main = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # متون با چیدمان مرکز‌چین
    draw.text((500, 250), "VOID ASCENSION", fill="#FFD700", font=font_main, anchor="mm")
    draw.text((500, 420), "THIS DOCUMENT CERTIFIES THAT", fill="#888888", font=font_sub, anchor="mm")
    draw.text((500, 520), f"\"{burden.upper()}\"", fill="#FFFFFF", font=font_main, anchor="mm")
    draw.text((500, 620), "HAS BEEN CONSUMED BY THE ETERNAL VOID", fill="#888888", font=font_sub, anchor="mm")
    
    # متادیتای پایین
    draw.text((500, 850), f"HOLDER ID: {user_id}", fill="#FFD700", font=font_sub, anchor="mm")
    draw.text((500, 910), "TIMESTAMP: 2025.VO-ID", fill="#333333", font=font_sub, anchor="mm")

    file_path = f"nft_{user_id}.png"
    image.save(file_path)
    return file_path
