import os
import random
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io

HF_TOKEN = os.getenv("HF_API_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# ۵۰ سبک رایگان (Eternal – لوکس و حرفه‌ای)
eternal_styles = [
    "luxurious dark royal certificate, golden ornate frame with diamonds, cosmic nebula background, sacred geometry mandala, elegant ancient gold font, masterpiece ultra-detailed",
    "imperial Byzantine icon style certificate, golden halo and intricate sacred geometry, dark void with stars, cinematic lighting, 8K",
    "Fabergé egg luxury certificate, golden enamel jewels plasma glow, cosmic void, divine aura, ultra-detailed",
    "Persian miniature royal decree, intricate gold arabesque, cosmic stars, sacred mandala, luxurious jewels",
    "Gothic obsidian seal, silver filigree dark nebula, celestial runes, masterpiece",
    # ... (۴۶ سبک دیگر – همه رویایی و لوکس)
    "Victorian holographic decree with steam-gold effects, dark cosmos background, elegant typography",
    "Celtic eternal knot crown with emerald glow, infinite cosmic void, sacred light",
    "Mughal emperor firman with diamond jali patterns, peacock throne glow, cosmic jewels",
    "Ancient Egyptian pharaoh scroll with lapis lazuli halo, star void, divine light",
    "Japanese imperial chrysanthemum seal with cherry blossom gold, eternal calm, masterpiece"
    # تا ۵۰ تا کامل
]

# ۱۰۰ سبک پولی (Divine, Celestial, Legendary – شاهانه و مسحورکننده)
premium_styles = [
    "absolute masterpiece divine portrait in Fabergé imperial egg style, golden enamel jewels plasma crown halo, cosmic void, sacred geometry, ultra-detailed 8K cinematic",
    "Byzantine holy icon divine portrait with golden halo and sacred mandala jewels, eternal light rays, masterpiece",
    "Persian shah miniature royal portrait with intricate gold illumination, cosmic nebula jewels, divine aura",
    "Renaissance da vinci divine portrait in golden frame with sacred light and cosmic harmony",
    "Baroque versailles royal portrait with pearl diamond crown, velvet void, cherub glow",
    "Mughal emperor divine portrait with peacock throne jewels, golden aura, cosmic mandala",
    "Egyptian pharaoh god-king portrait with ankh crown, lapis cosmic halo, eternal life",
    "Roman emperor laurel crown portrait with marble pillars, thunder glow, masterpiece",
    "Greek olympus god divine portrait with lightning halo, eternal flame, cosmic storm",
    "Japanese emperor chrysanthemum crown portrait with cherry blossom gold serenity, divine calm",
    # ... ۹۰ سبک دیگر – همه شاهانه، رویایی و اعتیادآور
    "Celestial knight starlight mithril armor portrait with divine halo and cosmic sword",
    "Legendary phoenix rebirth wings portrait with golden eternal flame and cosmic fire",
    "Divine oracle golden prophecy portrait with sacred vision light and eternal wisdom"
    # تا ۱۰۰ تا کامل
]

def generate_flux_image(prompt):
    payload = {
        "inputs": prompt,
        "parameters": {"num_inference_steps": 4, "guidance_scale": 3.5}
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return Image.open(io.BytesIO(response.content))
    return None

def overlay_text(img, burden, user_id, level, style_name):
    draw = ImageDraw.Draw(img)
    w, h = img.size

    try:
        title_font = ImageFont.truetype("arial.ttf", 100)
        burden_font = ImageFont.truetype("arial.ttf", 80)
        info_font = ImageFont.truetype("arial.ttf", 50)
    except:
        title_font = burden_font = info_font = ImageFont.load_default()

    gold = "#FFD700"
    white = "#FFFFFF"
    shadow = "#000000"

    draw.text((w//2, 200), "VOID ASCENSION", fill=gold, font=title_font, anchor="mm", stroke_width=5, stroke_fill=shadow)
    draw.text((w//2, h//2), f"“{burden.upper()}”", fill=white, font=burden_font, anchor="mm", stroke_width=4, stroke_fill=shadow)
    draw.text((w//2, h//2 + 150), f"LEVEL: {level}", fill=gold, font=info_font, anchor="mm", stroke_width=3, stroke_fill=shadow)
    draw.text((w//2, h - 300), f"Style: {style_name}", fill=gold, font=info_font, anchor="mm")
    draw.text((w//2, h - 200), f"Holder ID: {user_id}", fill=gold, font=info_font, anchor="mm")
    draw.text((w//2, h - 100), "2025.VO-ID", fill="#888888", font=info_font, anchor="mm")

    return img

def create_certificate(user_id, burden, level="Eternal", photo_path=None):
    if level == "Eternal":
        style_prompt = random.choice(eternal_styles)
    else:
        style_prompt = random.choice(premium_styles)

    full_prompt = f"{style_prompt}, burden \"{burden.upper()}\", level {level}, Holder ID {user_id}, 2025.VO-ID, dark luxury masterpiece 8K"

    img = generate_flux_image(full_prompt)

    if img:
        img = img.resize((1000, 1414), Image.LANCZOS)
        img = overlay_text(img, burden, user_id, level, "Custom Style")
        path = f"void_cert_{user_id}_{random.randint(10000,99999)}.png"
        img.save(path, "PNG", quality=95)
        return path, level
    return None, "Error"
