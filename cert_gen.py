from PIL import Image, ImageDraw, ImageFont, ImageFilter
import uuid
import os

def create_certificate(user_name: str, need_name: str) -> str:
    width, height = 1080, 1080 # مربع (مناسب برای پروفایل و NFT)
    img = Image.new('RGB', (width, height), color=(2, 2, 5))
    draw = ImageDraw.Draw(img)
    
    try:
        font_gold = ImageFont.truetype("font.ttf", 90)
        font_id = ImageFont.truetype("font.ttf", 30)
    except:
        font_gold = ImageFont.load_default()
        font_id = ImageFont.load_default()

    # ایجاد گرادینت طلایی در حاشیه
    draw.rectangle([20, 20, 1060, 1060], outline=(212, 175, 55), width=2)
    draw.rectangle([50, 50, 1030, 1030], outline=(212, 175, 55), width=1)

    # متن‌های لوکس
    draw.text((width/2, 200), "THE VOID", fill=(212, 175, 55), font=font_gold, anchor="mm")
    draw.text((width/2, 350), "NFT PROOF OF ABSTINENCE", fill=(100, 100, 100), font=font_id, anchor="mm")
    
    content = f"The burden of\n\n\"{need_name.upper()}\"\n\nhas been atomized."
    draw.multiline_text((width/2, height/2), content, fill=(255, 255, 255), font=font_gold, anchor="mm", align="center")
    
    # متادیتا (Metadata) شبیه‌سازی شده برای NFT
    serial = f"BLOCKCHAIN ID: TON-{uuid.uuid4().hex[:16].upper()}"
    draw.text((width/2, 900), serial, fill=(212, 175, 55), font=font_id, anchor="mm")
    draw.text((width/2, 950), "AUTHENTICATED BY THE VOID PROTOCOL", fill=(50, 50, 50), font=font_id, anchor="mm")

    filename = f"nft_{uuid.uuid4().hex[:8]}.png"
    img.save(filename)
    return filename
