from PIL import Image, ImageDraw, ImageFont
import os

def create_certificate(user_id, burden):
    # ایجاد یک بوم سیاه مربعی برای NFT
    width, height = 1000, 1000
    image = Image.new('RGB', (width, height), color='#000000')
    draw = ImageDraw.Draw(image)

    # طراحی حاشیه طلایی
    draw.rectangle([20, 20, 980, 980], outline='#FFD700', width=2)
    draw.rectangle([40, 40, 960, 960], outline='#FFD700', width=1)

    # بارگذاری فونت (اگر فونت نبود، از فونت پیش‌فرض استفاده می‌کند)
    try:
        font_large = ImageFont.truetype("arial.ttf", 60)
        font_small = ImageFont.truetype("arial.ttf", 30)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # نوشتن متون گواهی
    draw.text((width/2, 200), "VOID CERTIFICATE", fill="#FFD700", font=font_large, anchor="mm")
    draw.text((width/2, 400), "THIS IS TO CERTIFY THAT", fill="#AAAAAA", font=font_small, anchor="mm")
    draw.text((width/2, 500), f"'{burden.upper()}'", fill="#FFFFFF", font=font_large, anchor="mm")
    draw.text((width/2, 600), "HAS BEEN SUCCESSFULLY CONSUMED BY THE VOID", fill="#AAAAAA", font=font_small, anchor="mm")
    
    # متادیتای پایین گواهی
    draw.text((width/2, 850), f"OWNER ID: {user_id}", fill="#FFD700", font=font_small, anchor="mm")
    draw.text((width/2, 900), "STARDUST ASSET #2040", fill="#444444", font=font_small, anchor="mm")

    file_path = f"nft_{user_id}.png"
    image.save(file_path)
    return file_path
