import os
from PIL import Image, ImageDraw, ImageFont

def create_certificate(user_id, burden):
    # ایجاد بوم ۱۰۰۰ در ۱۰۰۰ پیکسل برای کیفیت بالا (NFT Style)
    width, height = 1000, 1000
    image = Image.new('RGB', (width, height), color='#000000')
    draw = ImageDraw.Draw(image)

    # طراحی حاشیه طلایی دو لایه (Luxury Look)
    draw.rectangle([20, 20, 980, 980], outline='#FFD700', width=4)
    draw.rectangle([45, 45, 955, 955], outline='#FFD700', width=1)

    # سیستم مدیریت فونت هوشمند برای جلوگیری از کرش در سرورهای لینوکس
    try:
        # آدرس‌های استاندارد فونت در سرورهای اوبونتو/دبیان
        font_main = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 65)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 35)
    except IOError:
        # اگر فونت در مسیر بالا نبود، از فونت پیش‌فرض استفاده می‌شود
        font_main = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # درج متون هنری
    draw.text((500, 250), "VOID ASCENSION", fill="#FFD700", font=font_main, anchor="mm")
    draw.text((500, 420), "THIS DOCUMENT CERTIFIES THAT", fill="#888888", font=font_sub, anchor="mm")
    
    # نمایش فداکاری کاربر با رنگ سفید درخشان
    draw.text((500, 520), f"\"{burden.upper()}\"", fill="#FFFFFF", font=font_main, anchor="mm")
    
    draw.text((500, 620), "HAS BEEN CONSUMED BY THE ETERNAL VOID", fill="#888888", font=font_sub, anchor="mm")
    
    # متادیتای اختصاصی
    draw.text((500, 850), f"HOLDER ID: {user_id}", fill="#FFD700", font=font_sub, anchor="mm")
    draw.text((500, 910), "TIMESTAMP: 2025.VO-ID", fill="#444444", font=font_sub, anchor="mm")

    file_path = f"nft_{user_id}.png"
    image.save(file_path)
    return file_path
