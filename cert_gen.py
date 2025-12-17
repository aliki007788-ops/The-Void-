from PIL import Image, ImageDraw, ImageFont
import uuid
import os

def create_certificate(user_name: str, need_name: str) -> str:
    """
    تولید گواهی لوکس The Void
    ورودی: نام کاربر (یا user_id) و نیاز/بار روانی
    خروجی: مسیر فایل PNG تولید شده
    """
    # ابعاد مناسب برای استوری/پست اینستاگرام
    width, height = 1080, 1350
    
    # زمینه مشکی عمیق
    img = Image.new('RGB', (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # بارگذاری فونت‌ها (اگر font.ttf نبود، از پیش‌فرض استفاده می‌کنه)
    try:
        font_gold = ImageFont.truetype("font.ttf", 80)      # برای عنوان و نیاز
        font_main = ImageFont.truetype("font.ttf", 50)      # متن اصلی
        font_id = ImageFont.truetype("font.ttf", 30)        # سریال
    except IOError:
        # اگر فونت پیدا نشد، از فونت پیش‌فرض سیستم استفاده کن
        font_gold = ImageFont.load_default()
        font_main = ImageFont.load_default()
        font_id = ImageFont.load_default()
    
    # کادر طلایی دور گواهی (لوکس و مینیمال)
    draw.rectangle([40, 40, width-40, height-40], outline=(255, 215, 0), width=5)
    
    # عنوان اصلی
    draw.text((width/2, 250), "THE VOID", fill=(255, 215, 0), font=font_gold, anchor="mm")
    
    # زیرعنوان
    draw.text((width/2, 450), "OFFICIAL ATTESTATION", fill=(200, 200, 200), font=font_main, anchor="mm")
    
    # متن گواهی
    content = f"This is to certify that\n\n{user_name.upper()}\n\nhas successfully surrendered the burden of:"
    draw.multiline_text((width/2, 650), content, fill=(255, 255, 255), font=font_main, anchor="mm", align="center", spacing=10)
    
    # نمایش نیاز با رنگ قرمز-طلایی پررنگ و علامت گیومه
    draw.text((width/2, 900), f"「 {need_name.upper()} 」", fill=(255, 0, 70), font=font_gold, anchor="mm")
    
    # شماره سریال منحصر به فرد (حس نایاب بودن)
    serial = f"VOID-ID: {uuid.uuid4().hex[:12].upper()}"
    draw.text((width/2, 1150), serial, fill=(100, 100, 100), font=font_id, anchor="mm")
    
    # ذخیره فایل با نام منحصر به فرد
    filename = f"cert_{uuid.uuid4().hex[:8]}.png"
    path = os.path.join(os.getcwd(), filename)
    img.save(path)
    
    return path
