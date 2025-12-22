import os
import random
import requests
import hashlib
import re
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io

# ========== CONFIG ==========
HF_TOKEN = os.getenv("HF_API_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# ========== 150 STYLE PROMPTS ==========

# سطح ۱: Eternal (۵۰ پرامپت)
ETERNAL_PROMPTS = [
    "luxurious dark royal portrait certificate with ornate golden arabesque frame, intricate diamonds and jewels, cosmic nebula background, sacred geometry mandala, elegant ancient gold font, ultra-detailed masterpiece cinematic lighting",
    "imperial Byzantine icon divine portrait with golden halo and intricate sacred geometry, dark cosmic void with stars, eternal light rays, ultra-detailed",
    "Fabergé egg luxury royal portrait with golden enamel jewels plasma glow, cosmic void, divine aura, intricate details, 8K masterpiece",
    "Persian miniature shah royal portrait with intricate gold illumination, cosmic stars, sacred mandala jewels, divine aura",
    "Gothic obsidian royal portrait seal with silver gold filigree, dark nebula, celestial runes luxury texture, cinematic",
    "Celtic eternal knot golden crown portrait with emerald jewels, infinite cosmic void, sacred light halo, masterpiece",
    "Art Nouveau flowing gold lines royal portrait with sapphire diamonds, ethereal cosmic background, elegant typography",
    "Mughal emperor divine portrait with diamond jali patterns, peacock throne glow, cosmic jewels mandala",
    "Victorian holographic royal portrait with steam-gold effects, dark cosmos nebula, luxurious velvet texture",
    "Ancient Egyptian pharaoh god-king portrait with lapis lazuli halo, golden ankh, cosmic stars eternal life",
    "Japanese imperial chrysanthemum crown portrait with cherry blossom gold, eternal calm serenity",
    "Roman laurel crown emperor portrait with marble pillars, thunder glow cosmic storm",
    "Renaissance illuminated manuscript divine portrait with divine light rays, golden vines sacred geometry",
    "Baroque Versailles royal portrait with pearl crown, dark velvet void cherub glow",
    "Rococo pearl gold luxury portrait with pastel nebula, intricate jewels divine light",
    "Steampunk void engine royal portrait with golden gears plasma energy cosmic dark luxury",
    "Cyberpunk neon gold holographic royal portrait with dark city cosmic void futuristic aura",
    "Dark fantasy dragon scale crown portrait with ruby eyes eternal fire halo cosmic void",
    "Nordic rune circle aurora borealis crown portrait with valhalla golden light sacred runes",
    "Aztec sun stone golden disk portrait with quetzalcoatl feathers cosmic calendar jewels",
    "Indian royal mandala lotus gold portrait with rainbow cosmic jewels divine enlightenment",
    "Chinese dragon emperor jade crown portrait with golden cloud nebula eternal power",
    "Greek Olympus god thunder halo portrait with marble cosmic void eternal flame",
    "Mayan king jade mask divine portrait with cosmic calendar golden serpent glow",
    "Tibetan thangka rainbow halo divine portrait with mandala jewels eternal peace",
    "Arabian nights aladdin lamp luxury royal portrait with genie smoke gold cosmic stars",
    "Atlantis crystal palace trident crown portrait with underwater divine glow jewels",
    "Avalon holy grail chalice portrait with mist eternal light halo",
    "Valhalla viking rune shield portrait with northern lights golden hammer glow",
    "Olympus thunder god lightning crown portrait with cosmic storm halo jewels",
    "Elven lothlórien mithril crown portrait with starlight glow ancient tree void",
    "Dwarven moria golden hall gemstone rune portrait with eternal forge fire",
    "Lost atlantis crystal gold decree portrait with underwater cosmic jewels",
    "Shambhala hidden kingdom rainbow jewel crown portrait with eternal peace halo",
    "Hyperborean eternal ice sun wheel crown portrait with aurora gold cosmic light",
    "Lemuria ancient wisdom pearl glow portrait with divine light rays",
    "Agartha inner earth crystal core golden portrait with eternal harmony aura",
    "Eden garden golden apple tree portrait with eternal divine light",
    "Mount meru cosmic axis jewel tier crown portrait with rainbow halo",
    "Asgard bifrost rainbow bridge gold portrait with eternal flame",
    "Vril energy plasma void rune portrait with sacred golden glow",
    "Thule hyperborean sun wheel ice crown portrait with eternal light",
    "Shinto torii kami golden light portrait with cosmic serenity",
    "Inca inti sun god golden disk portrait with mountain cosmic halo",
    "Sumerian anunnaki star gate cuneiform gold portrait with divine knowledge",
    "Babylonian ishtar lapis gold gate portrait with cosmic jewel aura",
    "Persian achaemenid immortal lion golden portrait with eternal guard halo",
    "Ottoman tuğra crescent moon jewel crown portrait with imperial glow",
    "Holy grail templar cross eternal quest portrait with divine light",
    "Philosopher's stone alchemical gold transmutation portrait with cosmic halo"
]

# سطح ۲: Divine (۴۰ پرامپت)
DIVINE_PROMPTS = [
    "absolute masterpiece divine portrait in Fabergé imperial egg style, golden enamel jewels plasma crown halo, cosmic void sacred geometry, ultra-detailed 8K cinematic",
    "Byzantine holy icon divine portrait with golden halo and sacred mandala jewels, eternal light rays masterpiece",
    "Persian shah miniature royal portrait with intricate gold illumination, cosmic nebula jewels divine aura",
    "Renaissance da vinci divine portrait in golden frame with sacred light cosmic harmony",
    "Baroque versailles royal portrait with pearl diamond crown velvet void cherub glow",
    "Mughal emperor divine portrait with peacock throne jewels golden aura cosmic mandala",
    "Egyptian pharaoh god-king portrait with ankh crown lapis cosmic halo eternal life",
    "Roman emperor laurel crown portrait with marble pillars thunder glow masterpiece",
    "Greek olympus god divine portrait with lightning halo eternal flame cosmic storm",
    "Japanese emperor chrysanthemum crown portrait with cherry blossom gold serenity divine calm",
    "Chinese dragon emperor divine portrait with jade crown golden cloud nebula eternal power",
    "Indian raja divine portrait with lotus crown rainbow mandala jewels enlightenment",
    "Celtic high king eternal knot crown portrait with emerald infinite glow",
    "Viking jarl valknut rune halo portrait with northern lights eternal fire",
    "Aztec eagle warrior quetzalcoatl feathers portrait with sun stone cosmic halo",
    "Inca sapa inca sun god mask portrait with golden disk mountain void",
    "Mayan king jade mask divine portrait with cosmic calendar jewels",
    "Tibetan dalai lama rainbow halo divine portrait with eternal peace mandala",
    "Ottoman sultan tuğra crescent moon crown portrait with jewel cosmic glow",
    "Russian tsar Fabergé crown imperial eagle portrait with eternal snow gold",
    "Victorian queen holographic crown portrait with steam-gold cosmic nebula",
    "Art nouveau flowing gold crown portrait with sapphire jewel ethereal light",
    "Gothic obsidian royal portrait with silver filigree dark nebula halo",
    "Rococo pearl crown divine portrait with pastel nebula cherub glow",
    "Steampunk void engine royal portrait with golden gears plasma energy",
    "Cyberpunk neon gold holographic royal portrait with dark city cosmic void",
    "Dark fantasy dragon scale crown portrait with ruby eyes eternal fire",
    "Nordic rune circle aurora borealis crown portrait with valhalla golden light",
    "Arabian nights aladdin lamp royal portrait with genie smoke gold cosmic stars",
    "Atlantis crystal trident crown portrait with underwater divine glow",
    "Avalon holy grail chalice portrait with mist eternal light halo",
    "Valhalla viking rune shield portrait with northern lights golden hammer",
    "Olympus thunder god lightning crown portrait with cosmic storm halo",
    "Elven lothlórien mithril crown portrait with starlight ancient tree glow",
    "Dwarven moria golden hall gemstone rune portrait with eternal forge fire",
    "Lost atlantis crystal gold decree portrait with underwater cosmic jewels",
    "Shambhala hidden kingdom rainbow jewel crown portrait with eternal peace",
    "Hyperborean eternal ice sun wheel crown portrait with aurora gold",
    "Lemuria ancient wisdom pearl glow portrait with divine light rays",
    "Agartha inner earth crystal core golden portrait with eternal harmony"
]

# سطح ۳: Celestial (۳۰ پرامپت)
CELESTIAL_PROMPTS = [
    "celestial phoenix rebirth wings portrait with golden eternal flame cosmic fire divine aura masterpiece",
    "sacred geometry infinite flower of life golden portrait with cosmic harmony mandala ultra-detailed",
    "sovereign imperial diamond plasma crown portrait with eternal sovereign glow cosmic jewels",
    "void obsidian throne emperor portrait with infinite dark halo cosmic jewels masterpiece",
    "celestial aurora guardian portrait with eternal protection rainbow halo divine light",
    "divine sacred vision oracle portrait with golden prophecy light eternal wisdom aura",
    "eternal cosmic rebellion prometheus portrait with divine fire halo infinite power",
    "royal dark sun eclipse portrait with shadow jewel crown cosmic glow masterpiece",
    "eternal imperial dragon portrait with jade power cosmic clouds eternal flame",
    "divine pearl lotus bloom portrait with rainbow purity glow eternal enlightenment",
    "golden eternal pharaoh portrait with ankh life lapis halo cosmic stars",
    "honor samurai eternal sword portrait with chrysanthemum light eternal warrior aura",
    "warrior void spartan portrait with rune shield eternal fire infinite battle glow",
    "starlight celestial knight portrait with mithril divine armor cosmic sword halo",
    "rebirth phoenix divine wings portrait with golden eternal flame cosmic fire",
    "infinite sacred geometry portrait with flower life cosmic gold divine harmony",
    "sovereign imperial diamond portrait with plasma eternal crown cosmic jewels",
    "infinite void obsidian portrait with dark emperor throne halo eternal",
    "eternal celestial guardian portrait with aurora protection rainbow divine light",
    "prophecy divine oracle portrait with sacred golden vision eternal wisdom",
    "rebellion eternal prometheus portrait with cosmic divine fire infinite power",
    "shadow royal eclipse portrait with dark sun jewel crown cosmic glow",
    "eternal imperial dragon portrait with jade power cosmic clouds",
    "divine pearl lotus portrait with rainbow purity glow eternal",
    "golden eternal pharaoh portrait with ankh life lapis halo",
    "honor samurai eternal sword portrait with chrysanthemum light",
    "warrior void spartan portrait with rune shield eternal fire",
    "starlight celestial knight portrait with mithril divine armor",
    "rebirth phoenix divine wings portrait with golden eternal flame",
    "infinite sacred geometry portrait with flower life cosmic gold"
]

# سطح ۴: Legendary (۳۰ پرامپت)
LEGENDARY_PROMPTS = [
    "legendary void emperor infinite darkness throne with cosmic plasma jewels eternal crown masterpiece ultra-detailed",
    "ultimate divine phoenix eternal rebirth with golden wings cosmic fire halo infinite power",
    "legendary sacred geometry flower of life infinite golden mandala with divine light rays masterpiece",
    "imperial diamond plasma sovereign crown with eternal glow cosmic jewels ultra-detailed",
    "legendary celestial guardian aurora rainbow protection halo with eternal harmony divine light",
    "divine oracle golden prophecy sacred vision light with eternal wisdom aura masterpiece",
    "eternal prometheus cosmic rebellion divine fire halo with infinite power masterpiece",
    "royal dark sun eclipse shadow jewel crown with cosmic void glow ultra-detailed",
    "legendary imperial dragon jade power cosmic clouds with eternal flame masterpiece",
    "divine pearl lotus rainbow purity bloom with eternal enlightenment halo ultra-detailed",
    "golden eternal pharaoh ankh life lapis crown with cosmic stars masterpiece",
    "legendary samurai honor sword chrysanthemum light with eternal warrior aura ultra-detailed",
    "void spartan rune shield eternal fire with infinite battle glow masterpiece",
    "celestial knight starlight mithril divine armor with cosmic sword halo ultra-detailed",
    "legendary phoenix rebirth wings golden eternal flame cosmic fire masterpiece",
    "infinite sacred geometry flower life cosmic gold with divine harmony ultra-detailed",
    "sovereign imperial diamond plasma eternal crown with cosmic jewels masterpiece",
    "infinite void obsidian dark emperor throne with eternal halo ultra-detailed",
    "eternal celestial guardian aurora rainbow protection with divine light masterpiece",
    "prophecy divine oracle sacred golden vision with eternal wisdom masterpiece",
    "rebellion eternal prometheus cosmic divine fire with infinite power ultra-detailed",
    "shadow royal eclipse dark sun jewel crown with cosmic glow masterpiece",
    "eternal imperial dragon jade cosmic clouds with power flame ultra-detailed",
    "divine pearl lotus rainbow purity eternal bloom masterpiece",
    "golden eternal pharaoh ankh lapis cosmic life halo ultra-detailed",
    "legendary samurai eternal sword honor chrysanthemum light masterpiece",
    "warrior void spartan eternal rune shield fire ultra-detailed",
    "starlight celestial knight mithril divine armor cosmic masterpiece",
    "rebirth phoenix golden wings eternal flame divine ultra-detailed",
    "infinite sacred geometry cosmic gold flower life harmony masterpiece"
]

# ========== HELPER FUNCTIONS ==========

def sanitize_burden(text: str) -> str:
    """پاکسازی ورودی burden از کاراکترهای خطرناک"""
    if not text or not isinstance(text, str):
        return "Eternal Sovereign"
    
    # حذف کاراکترهای خطرناک
    clean = re.sub(r'[<>"\'\&;\\/\[\]{}()|`~]', '', text)
    
    # محدودیت طول (۵۰ کاراکتر)
    clean = clean[:50]
    
    # جایگزینی چند فاصله با یک فاصله
    clean = ' '.join(clean.split())
    
    return clean.strip() or "Eternal Sovereign"

def validate_image(file_path: str) -> bool:
    """اعتبارسنجی عکس آپلودشده"""
    try:
        with Image.open(file_path) as img:
            # بررسی فرمت
            if img.format not in ['JPEG', 'PNG', 'WEBP']:
                return False
            
            # بررسی سایز (حداکثر 10 مگاپیکسل)
            if img.size[0] * img.size[1] > 10000000:
                return False
            
            # بررسی corrupt نبودن
            img.verify()
            return True
            
    except Exception as e:
        print(f"Image validation error: {e}")
        return False

def generate_dna(user_id: int, burden: str, level: str) -> str:
    """تولید کد DNA منحصربه‌فرد برای هر گواهی"""
    seed = f"{user_id}{burden}{level}{datetime.now().isoformat()}{random.randint(1000, 9999)}"
    hash_obj = hashlib.sha256(seed.encode())
    return hash_obj.hexdigest()[:16].upper()

def generate_ai_image(prompt: str, init_image_path: str = None):
    """تولید تصویر با هوش مصنوعی"""
    try:
        if init_image_path and os.path.exists(init_image_path):
            # حالت img2img - با عکس کاربر
            with open(init_image_path, "rb") as f:
                image_data = f.read()
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "strength": 0.5,
                    "guidance_scale": 8,
                    "num_inference_steps": 45,
                    "negative_prompt": "blurry, distorted, ugly, bad quality, watermark, text"
                }
            }
            
            response = requests.post(
                API_URL,
                headers=headers,
                files={"image": image_data},
                data=payload,
                timeout=60
            )
            
        else:
            # حالت text-to-image - بدون عکس
            payload = {
                "inputs": prompt,
                "parameters": {
                    "guidance_scale": 8,
                    "num_inference_steps": 45,
                    "negative_prompt": "blurry, distorted, ugly, bad quality, watermark, text"
                }
            }
            
            response = requests.post(
                API_URL,
                headers=headers,
                json=payload,
                timeout=60
            )
        
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
        else:
            print(f"AI API Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return None
            
    except requests.exceptions.Timeout:
        print("AI API timeout")
        return None
    except Exception as e:
        print(f"AI generation error: {e}")
        return None

def add_text_to_image(img, burden: str, user_id: int, level: str, dna: str):
    """افزودن متن روی تصویر گواهی"""
    try:
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        # تلاش برای بارگذاری فونت‌ها
        try:
            # ابتدا فونت‌های سیستم را امتحان کن
            font_paths = [
                "arial.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
                "C:\\Windows\\Fonts\\arial.ttf"
            ]
            
            title_font = None
            for path in font_paths:
                if os.path.exists(path):
                    try:
                        title_font = ImageFont.truetype(path, 80)
                        break
                    except:
                        continue
            
            if title_font is None:
                title_font = ImageFont.load_default()
                
            burden_font = ImageFont.truetype(path, 60) if title_font != ImageFont.load_default() else ImageFont.load_default()
            info_font = ImageFont.truetype(path, 35) if title_font != ImageFont.load_default() else ImageFont.load_default()
            
        except:
            # فونت پیش‌فرض
            title_font = burden_font = info_font = ImageFont.load_default()
        
        # رنگ‌ها
        gold = "#FFD700"
        gold_light = "#FFEC8B"
        white = "#FFFFFF"
        shadow = "#000000"
        gray = "#888888"
        
        # سایه برای متن
        def draw_text_with_shadow(x, y, text, font, fill, shadow_fill, shadow_offset=3):
            draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_fill, anchor="mm")
            draw.text((x, y), text, font=font, fill=fill, anchor="mm")
        
        # عنوان اصلی
        draw_text_with_shadow(
            width // 2, 180,
            "VOID ASCENSION",
            title_font, gold, shadow, 4
        )
        
        # Burden
        draw_text_with_shadow(
            width // 2, height // 2,
            f"\"{burden.upper()}\"",
            burden_font, white, shadow, 3
        )
        
        # سطح
        draw_text_with_shadow(
            width // 2, height // 2 + 130,
            f"LEVEL: {level}",
            info_font, gold_light, shadow, 2
        )
        
        # استایل
        draw_text_with_shadow(
            width // 2, height - 280,
            "Style: Eternal Void",
            info_font, gold, shadow, 2
        )
        
        # شناسه کاربر
        draw_text_with_shadow(
            width // 2, height - 220,
            f"Holder ID: {user_id}",
            info_font, gold, shadow, 2
        )
        
        # DNA
        draw.text(
            (width // 2, height - 160),
            f"DNA: {dna}",
            font=info_font,
            fill=gray,
            anchor="mm"
        )
        
        # تاریخ
        draw.text(
            (width // 2, height - 100),
            f"Date: {datetime.now().strftime('%Y.%m.%d')}",
            font=info_font,
            fill=gray,
            anchor="mm"
        )
        
        # کپی رایت
        draw.text(
            (width // 2, height - 40),
            "2025.VO-ID | THE ETERNAL ARCHIVE",
            font=info_font,
            fill="#555555",
            anchor="mm"
        )
        
        return img
        
    except Exception as e:
        print(f"Text overlay error: {e}")
        return img

def create_certificate(user_id: int, burden: str, level: str = "Eternal", photo_path: str = None):
    """تابع اصلی ایجاد گواهینامه"""
    try:
        print(f"Creating certificate for user {user_id}, level {level}")
        
        # ۱. پاکسازی burden
        burden = sanitize_burden(burden)
        print(f"Sanitized burden: {burden}")
        
        # ۲. تولید DNA
        dna = generate_dna(user_id, burden, level)
        print(f"Generated DNA: {dna}")
        
        # ۳. انتخاب پرامپت بر اساس سطح
        if level == "Eternal":
            style_prompt = random.choice(ETERNAL_PROMPTS)
        elif level == "Divine":
            style_prompt = random.choice(DIVINE_PROMPTS)
        elif level == "Celestial":
            style_prompt = random.choice(CELESTIAL_PROMPTS)
        else:  # Legendary
            style_prompt = random.choice(LEGENDARY_PROMPTS)
        
        # ۴. ساخت پرامپت نهایی
        full_prompt = f"{style_prompt}, burden: \"{burden}\", level: {level}, royal portrait certificate, ultra detailed, masterpiece, cinematic lighting, dark luxury, 8K, professional"
        print(f"Full prompt length: {len(full_prompt)}")
        
        # ۵. اعتبارسنجی عکس
        if photo_path and not validate_image(photo_path):
            print("Invalid photo, using text-to-image")
            photo_path = None
        
        # ۶. تولید تصویر با AI
        print("Generating AI image...")
        img = generate_ai_image(full_prompt, photo_path)
        
        if img is None:
            print("AI generation failed, creating fallback image")
            # تصویر fallback
            img = Image.new('RGB', (1000, 1400), color='#0A0A0A')
            
            # اضافه کردن gradient ساده
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            for i in range(1400):
                color_value = int(10 + (i / 1400 * 50))
                draw.line([(0, i), (1000, i)], fill=(color_value, color_value, color_value))
        
        # ۷. تغییر سایز به استاندارد
        img = img.resize((1000, 1400), Image.Resampling.LANCZOS)
        print(f"Image resized to: {img.size}")
        
        # ۸. افزودن متن
        print("Adding text overlay...")
        img = add_text_to_image(img, burden, user_id, level, dna)
        
        # ۹. ذخیره فایل
        os.makedirs("temp_certs", exist_ok=True)
        output_path = f"temp_certs/cert_{user_id}_{dna}.png"
        
        # ذخیره با کیفیت بالا
        img.save(output_path, "PNG", optimize=True, quality=95)
        print(f"Certificate saved to: {output_path}")
        
        # ۱۰. بررسی سایز فایل
        file_size = os.path.getsize(output_path) / 1024  # KB
        print(f"File size: {file_size:.1f} KB")
        
        if file_size > 5000:  # بیشتر از ۵ مگابایت
            print("File too large, re-saving with compression...")
            img.save(output_path, "PNG", optimize=True, quality=85)
        
        return output_path, level
        
    except Exception as e:
        print(f"Error in create_certificate: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, "Error"

# ========== TEST FUNCTION ==========
if __name__ == "__main__":
    # تست تابع
    print("Testing certificate generation...")
    
    # ایجاد یک گواهی تست
    test_path, test_level = create_certificate(
        user_id=123456,
        burden="Test Eternal Burden",
        level="Eternal"
    )
    
    if test_path:
        print(f"✓ Test successful! Certificate created at: {test_path}")
        print(f"✓ Level: {test_level}")
    else:
        print("✗ Test failed!")
