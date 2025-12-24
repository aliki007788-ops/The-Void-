import os
import random
import requests
import io
import hashlib
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# --- تنظیمات اتصال به هوش مصنوعی ---
HF_TOKEN = os.getenv("HF_API_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# --- بانک ۱۵۰ سبک حرفه‌ای بر اساس نایابی (Rarity) ---

PROMPTS = {
    "Eternal": [ # ۶۰ سبک لوکس و کلاسیک (رایگان)
        f"luxurious {c} obsidian texture, thin gold filigree, {l} lighting, intricate ornaments, 8k resolution, masterpiece" 
        for c in ["dark", "polished", "matte", "ancient", "royal", "ebony", "charcoal", "midnight", "deep onyx", "velvet black"] 
        for l in ["cinematic", "soft glowing", "mystical rays", "dramatic shadows", "ethereal", "golden hour"]
    ][:60],

    "Divine": [ # ۴۰ سبک امپراتوری و بیزانسی (ویژه)
        f"imperial Byzantine mosaic, {g} leaf embroidery, sacred {a} aura, religious iconography style, high-detail gold, masterpiece art" 
        for g in ["heavy gold", "shining golden", "distressed antique gold", "liquid gold", "rose gold"]
        for a in ["divine", "ethereal", "majestic", "heavenly", "saintly", "eternal", "sovereign", "regal"]
    ][:40],

    "Celestial": [ # ۴۰ سبک کیهانی و ماورایی (نایاب)
        f"celestial {e} nebula background, cosmic gold dust, {s} sacred geometry, astral light flows, hyper-detailed cosmic art" 
        for e in ["phoenix", "galaxy", "stardust", "void", "supernova", "black hole", "interstellar", "constellation"]
        for s in ["infinite", "transcendental", "mystic", "geometric", "ancient"]
    ][:40],

    "Legendary": [ # ۱۰ سبک فوق نایاب (امپراتور خلأ - ۱ درصد شانس)
        "supreme void emperor, throne made of dying stars and liquid gold, hyper-realistic 16k, dark luxury",
        "omega singularity point, golden light shattering the fabric of reality, cinematic masterpiece, epic scale",
        "ultimate god-like entity of the void, wings of golden fire and obsidian, 8k wide angle, dramatic",
        "the heart of creation, golden geometric infinity, transcendental cosmic art, masterpiece, high contrast",
        "legendary solar dragon, scales of molten gold reflecting galaxies, deep space void art, intricate detail",
        "ascension climax, a mortal soul turning into golden stardust, spiritual awakening, 16k, heavenly glow",
        "ancient cosmic observer, eye of the void, pupils of golden suns, epic scale art, mythological",
        "the golden gate of eternity, floating in a sea of black liquid gold, highly detailed, photorealistic",
        "primordial deity of gold, liquid light forming a divine body, ethereal lighting 16k, magnificent",
        "absolute legendary void artifact, golden light explosion in total darkness, cinematic, 8k"
    ]
}

def generate_dna(user_id, level):
    """تولید کد اختصاصی ۱۰ رقمی برای شناسایی در اتاق حراجی و تالار افتخارات"""
    seed = f"{user_id}{level}{datetime.now().isoformat()}".encode()
    return hashlib.sha256(seed).hexdigest()[:10].upper()

def create_certificate(user_id, burden, level="Eternal", user_photo_path=None):
    """تابع اصلی تولید گواهینامه با استفاده از هوش مصنوعی و پردازش تصویر"""
    
    # ۱. انتخاب تصادفی یک سبک از بین لیست ۱۵۰تایی بر اساس سطح دسترسی
    style_list = PROMPTS.get(level, PROMPTS["Eternal"])
    selected_style = random.choice(style_list)
    
    # ۲. ترکیب فداکاری کاربر با سبک انتخاب شده (Prompt Engineering)
    # اضافه کردن کلمات کلیدی برای افزایش کیفیت خروجی SD v1.5
    full_prompt = f"{selected_style}, focal point, hyper-detailed, golden and dark theme, sharp focus, 8k, photorealistic, elegant composition"

    # ۳. فراخوانی API هوش مصنوعی برای تولید تصویر پایه
    try:
        payload = {
            "inputs": full_prompt,
            "parameters": {"num_inference_steps": 50, "guidance_scale": 7.5}
        }
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            image = Image.open(io.BytesIO(response.content))
        else:
            print(f"API Error {response.status_code}: Creating fallback background")
            image = Image.new('RGB', (1000, 1414), color='#050505')
    except Exception as e:
        print(f"Connection Error: {e}")
        image = Image.new('RGB', (1000, 1414), color='#050505')

    # ۴. تنظیم اندازه تصویر و آماده‌سازی برای متن‌نویسی
    canvas = image.resize((1000, 1414), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(canvas)
    dna = generate_dna(user_id, level)

    # ۵. لود کردن فونت (مطمئن شوید فایل فونت در کنار این اسکریپت باشد)
    try:
        # ترجیحاً از فونت Cinzel یا فونت‌های سریف کلاسیک استفاده کنید
        font_main = ImageFont.truetype("cinzel.ttf", 60)
        font_sub = ImageFont.truetype("cinzel.ttf", 35)
        font_dna = ImageFont.truetype("arial.ttf", 30)
    except:
        # در صورت نبود فونت، از فونت پیش‌فرض سیستم استفاده می‌شود
        font_main = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_dna = ImageFont.load_default()

    # ۶. چاپ متن‌ها با افکت سایه برای خوانایی بهتر روی تصویر AI
    # مرکز صفحه
    w, h = canvas.size
    
    # عنوان اصلی (بالا)
    draw.text((w/2 + 2, 180 + 2), "VOID ASCENSION", fill="black", font=font_main, anchor="mm") # سایه
    draw.text((w/2, 180), "VOID ASCENSION", fill="#D4AF37", font=font_main, anchor="mm") # طلایی اصلی

    # متن Burden کاربر (مرکز)
    draw.text((w/2, h/2), f"“ {burden.upper()} ”", fill="white", font=font_sub, anchor="mm")
    
    # اطلاعات نایابی و امنیتی (پایین)
    draw.text((w/2, h - 220), f"LEVEL: {level.upper()}", fill="#D4AF37", font=font_sub, anchor="mm")
    draw.text((w/2, h - 160), f"DNA: {dna}", fill="#888888", font=font_dna, anchor="mm")
    draw.text((w/2, h - 100), f"ISSUED BY THE VOID ARCHIVE", fill="#444444", font=font_dna, anchor="mm")

    # ۷. ذخیره خروجی نهایی
    output_dir = "static/outputs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    final_path = f"{output_dir}/cert_{dna}.png"
    canvas.save(final_path, "PNG", quality=95)
    
    return final_path, dna
