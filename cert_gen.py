from PIL import Image, ImageDraw, ImageFont
import uuid
import os

def create_certificate(user_id: str, burden: str) -> str:
    # ابعاد استاندارد NFT (مربع ۱:۱)
    width, height = 1080, 1080
    # ایجاد پس‌زمینه مشکی عمیق
    img = Image.new('RGB', (width, height), color=(2, 2, 5))
    draw = ImageDraw.Draw(img)
    
    # تلاش برای بارگذاری فونت (در صورت نبودن از فونت پیش‌فرض استفاده می‌شود)
    try:
        font_large = ImageFont.truetype("font.ttf", 80)
        font_small = ImageFont.truetype("font.ttf", 35)
        font_serial = ImageFont.truetype("font.ttf", 25)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_serial = ImageFont.load_default()

    # رسم حاشیه طلایی دو لایه (Luxury Border)
    draw.rectangle([30, 30, 1050, 1050], outline=(212, 175, 55), width=3)
    draw.rectangle([50, 50, 1030, 1030], outline=(212, 175, 55), width=1)

    # متون اصلی
    draw.text((width/2, 200), "CERTIFICATE OF ATOMIZATION", fill=(212, 175, 55), font=font_small, anchor="mm")
    
    content = f"The Cosmic Void has consumed\n\n\"{burden.upper()}\"\n\nfrom the consciousness of\nUser ID: {user_id}"
    draw.multiline_text((width/2, height/2), content, fill=(255, 255, 255), font=font_large, anchor="mm", align="center")
    
    # بخش NFT (شماره سریال و امضای دیجیتال)
    serial_number = f"ASSET ID: VOID-{uuid.uuid4().hex[:12].upper()}"
    draw.text((width/2, 850), serial_number, fill=(212, 175, 55), font=font_serial, anchor="mm")
    draw.text((width/2, 900), "STATUS: MINTED ON ETERNITY", fill=(100, 100, 100), font=font_serial, anchor="mm")
    draw.text((width/2, 950), "PROTOCOL: V.2040-NULL", fill=(50, 50, 50), font=font_serial, anchor="mm")

    filename = f"nft_cert_{user_id}.png"
    img.save(filename)
    return filename
