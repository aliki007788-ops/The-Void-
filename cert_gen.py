From PIL import Image, ImageDraw, ImageFont
Import uuid

Def create_certificate(user_name, need_name):
    # ابعاد اینستاگرام (1080x1350)
    Width, height = 1080, 1350
    Img = Image.new('RGB', (width, height), color=(0, 0, 0))
    Draw = ImageDraw.Draw(img)
    
    # بارگذاری فونت (مطمئن شوید فایل font.ttf در پوشه هست)
    Try:
        Font_gold = ImageFont.truetype("font.ttf", 80)
        Font_main = ImageFont.truetype("font.ttf", 50)
        Font_id = ImageFont.truetype("font.ttf", 30)
    Except:
        Font_gold = font_main = font_id = ImageFont.load_default()

    # طراحی کادر طلایی دور گواهی
    Draw.rectangle([40, 40, 1040, 1310], outline=(255, 215, 0), width=5)
    
    # متن‌ها
    Draw.text((width/2, 250), "THE VOID", fill=(255, 215, 0), font=font_gold, anchor="mm")
    Draw.text((width/2, 450), "OFFICIAL ATTESTATION", fill=(200, 200, 200), font=font_main, anchor="mm")
    
    Content = f"This is to certify that\n\n{user_name.upper()}\n\nhas successfully surrendered the burden of:"
    Draw.multiline_text((width/2, 650), content, fill=(255, 255, 255), font=font_main, anchor="mm", align="center")
    
    # نمایش نیاز با فونت درشت و قرمز/طلایی
    Draw.text((width/2, 900), f"「 {need_name.upper()} 」", fill=(255, 0, 70), font=font_gold, anchor="mm")
    
    # شماره سریال منحصر به فرد (برای القای حس نایاب بودن)
    Serial = f"VOID-ID: {uuid.uuid4().hex[:12].upper()}"
    Draw.text((width/2, 1150), serial, fill=(100, 100, 100), font=font_id, anchor="mm")
    
    Path = f"cert_{user_name}.png"
    Img.save(path)
    Return path