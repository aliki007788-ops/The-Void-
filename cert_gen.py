import os
import random
import requests
import hashlib
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# --- تنظیمات اتصال به هوش مصنوعی ---
# حتماً TOKEN خود را در محیط سیستم (Environment Variable) تعریف کنید
HF_TOKEN = os.getenv("HF_API_TOKEN", "YOUR_HF_TOKEN_HERE")
API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# --- دیتابیس پرامپت‌های مهندسی شده (۱۵۰ استایل) ---

eternal_styles = [
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

divine_styles = [
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

celestial_styles = [
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

legendary_styles = [
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

# --- توابع کمکی ---

def generate_dna(user_id, burden, level):
    data = f"{user_id}{burden}{level}{datetime.now().isoformat()}"
    return hashlib.sha256(data.encode()).hexdigest()[:16].upper()

def overlay_premium_text(img, burden, user_id, level, dna):
    """
    درج متن با استایل لوکس، سایه و فونت‌های سنگین برای خوانایی روی تصویر AI.
    """
    draw = ImageDraw.Draw(img)
    w, h = img.size
    
    # بارگذاری فونت (اطمینان حاصل کنید فایل فونت در کنار پروژه باشد یا مسیر صحیح بدهید)
    try:
        # استفاده از فونت Cinzel برای حس کلاسیک و لوکس (پیشنهادی)
        title_f = ImageFont.truetype("Cinzel-Bold.ttf", 80)
        main_f = ImageFont.truetype("Cinzel-Regular.ttf", 55)
        sub_f = ImageFont.truetype("Cinzel-Regular.ttf", 35)
    except:
        # فونت پیش‌فرض لینوکس اگر فونت بالا پیدا نشد
        try:
            title_f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
            main_f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 45)
            sub_f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
        except:
            title_f = main_f = sub_f = ImageFont.load_default()

    gold_color = "#D4AF37"
    white_color = "#FFFFFF"
    shadow_color = "#000000"

    # ۱. عنوان اصلی با سایه (Void Ascension)
    draw.text((w//2 + 3, 180 + 3), "VOID ASCENSION", fill=shadow_color, font=title_f, anchor="mm")
    draw.text((w//2, 180), "VOID ASCENSION", fill=gold_color, font=title_f, anchor="mm")

    # ۲. متن فداکاری (Burden) در مرکز
    # پیچیدن متن اگر طولانی باشد
    max_w = w - 200
    words = burden.upper().split()
    lines = []
    current_line = ""
    for word in words:
        if draw.textbbox((0,0), current_line + word, font=main_f)[2] < max_w:
            current_line += word + " "
        else:
            lines.append(current_line.strip())
            current_line = word + " "
    lines.append(current_line.strip())

    y_text = h // 2
    for line in lines:
        draw.text((w//2, y_text), f"“ {line} ”", fill=white_color, font=main_f, anchor="mm")
        y_text += 70

    # ۳. جزئیات پایین (Level, Holder, DNA)
    footer_y = h - 220
    draw.text((w//2, footer_y), f"LEVEL: {level.upper()}", fill=gold_color, font=sub_f, anchor="mm")
    draw.text((w//2, footer_y + 55), f"HOLDER: {user_id}", fill=white_color, font=sub_f, anchor="mm")
    draw.text((w//2, footer_y + 105), f"DNA: {dna}", fill="#AAAAAA", font=sub_f, anchor="mm")

    return img

def create_certificate(user_id, burden, level="Eternal", photo_path=None):
    """
    تابع اصلی برای تولید گواهی با استفاده از Stable Diffusion 1.5
    """
    styles_map = {
        "Eternal": eternal_styles,
        "Divine": divine_styles,
        "Celestial": celestial_styles,
        "Legendary": legendary_styles
    }
    
    style_list = styles_map.get(level, eternal_styles)
    selected_base_prompt = random.choice(style_list)
    
    # تقویت پرامپت نهایی برای تضمین کیفیت
    full_prompt = (
        f"{selected_base_prompt}, centered artistic composition, obsidian and gold theme, "
        f"8k resolution, cinematic lighting, sharp focus, volumetric light"
    )

    dna = generate_dna(user_id, burden, level)

    payload = {
        "inputs": full_prompt,
        "parameters": {
            "num_inference_steps": 50, 
            "guidance_scale": 9.0,
            "negative_prompt": "text, watermark, logo, blurry, low resolution, distorted, ugly, deformed"
        }
    }
    
    img = None
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
        else:
            print(f"AI API Error: {response.status_code}")
    except Exception as e:
        print(f"Request Error: {e}")

    # ایجاد یک تصویر بک‌آپ اگر هوش مصنوعی پاسخ نداد
    if not img:
        img = Image.new('RGB', (1000, 1414), '#0a0a0a')
        draw = ImageDraw.Draw(img)
        # ایجاد یک گرادینت ساده یا الگو برای تصویر بک‌آپ
        for i in range(0, 1414, 10):
            draw.line([(0, i), (1000, i)], fill="#111", width=1)

    # تغییر اندازه به رزولوشن استاندارد چاپ
    img = img.resize((1000, 1414), Image.Resampling.LANCZOS)
    
    # اعمال لایه‌های متن لوکس
    img = overlay_premium_text(img, burden, user_id, level, dna)
    
    # ذخیره‌سازی
    os.makedirs("outputs", exist_ok=True)
    file_path = f"outputs/void_{user_id}_{dna}.png"
    img.save(file_path, "PNG", quality=95)
    
    return file_path, dna

# --- تست سریع (اختیاری) ---
if __name__ == "__main__":
    # اگر این فایل را مستقیماً اجرا کنید، یک تست می‌گیرد
    print("Testing Divine Generation...")
    path, dna = create_certificate(12345, "I surrender my fears to the void", "Legendary")
    print(f"Test Completed! Image saved at: {path}")
