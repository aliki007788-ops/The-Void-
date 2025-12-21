import os
import random
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io

HF_TOKEN = os.getenv("HF_API_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"  # بهترین img2img رایگان

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# ۵۰ سبک رایگان (لوکس و حرفه‌ای)
eternal_styles = [
    "luxurious royal certificate, ornate golden frame with diamonds and jewels, dark cosmic background with nebula, sacred geometry mandala, elegant gold text, ultra-detailed masterpiece",
    "imperial Byzantine icon style certificate, golden halo, intricate sacred geometry, dark void with stars, cinematic lighting",
    "Fabergé egg luxury certificate, golden enamel with jewels, plasma glow, cosmic void, divine aura",
    "Persian miniature royal decree, intricate gold arabesque, cosmic stars, sacred mandala",
    "Gothic obsidian seal, silver filigree, dark nebula, celestial runes",
    # ... (۵۰ تا کامل)
]

# ۱۰۰ سبک پولی (شاهانه و رویایی)
premium_styles = [
    "absolute masterpiece divine portrait in Fabergé imperial egg style, golden enamel jewels plasma crown halo, cosmic void, sacred geometry, ultra-detailed 8K",
    "Byzantine holy icon divine portrait with golden halo and sacred mandala jewels, eternal light rays",
    "Persian shah miniature royal portrait with intricate gold illumination, cosmic nebula jewels",
    # ... (۱۰۰ تا کامل)
]

def generate_img2img(prompt, init_image_path):
    with open(init_image_path, "rb") as f:
        init_image = f.read()
    
    payload = {
        "prompt": prompt,
        "init_image": init_image,
        "strength": 0.5,  # چهره واقعی حفظ بشه
        "guidance_scale": 9,
        "num_inference_steps": 50
    }
    
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return Image.open(io.BytesIO(response.content))
    return None

def overlay_text(img, burden, user_id, level):
    draw = ImageDraw.Draw(img)
    w, h = img.size
    try:
        title_font = ImageFont.truetype("arial.ttf", 90)
        burden_font = ImageFont.truetype("arial.ttf", 70)
        info_font = ImageFont.truetype("arial.ttf", 45)
    except:
        title_font = burden_font = info_font = ImageFont.load_default()

    gold = "#FFD700"
    white = "#FFFFFF"
    shadow = "#000000"

    draw.text((w//2, 200), "VOID ASCENSION", fill=gold, font=title_font, anchor="mm", stroke_width=5, stroke_fill=shadow)
    draw.text((w//2, h//2), f"“{burden.upper()}”", fill=white, font=burden_font, anchor="mm", stroke_width=4, stroke_fill=shadow)
    draw.text((w//2, h//2 + 150), f"LEVEL: {level}", fill=gold, font=info_font, anchor="mm")
    draw.text((w//2, h - 300), "Style: Custom Void", fill=gold, font=info_font, anchor="mm")
    draw.text((w//2, h - 200), f"Holder ID: {user_id}", fill=gold, font=info_font, anchor="mm")
    draw.text((w//2, h - 100), "2025.VO-ID", fill="#888888", font=info_font, anchor="mm")

    return img

def create_certificate(user_id, burden, level="Eternal", photo_path=None):
    if level == "Eternal":
        style_prompt = random.choice(eternal_styles)
    else:
        style_prompt = random.choice(premium_styles)
    
    full_prompt = f"{style_prompt}, burden \"{burden.upper()}\", level {level}, ultra-detailed masterpiece, cinematic lighting, dark luxury royal certificate"

    if photo_path:
        img = generate_img2img(full_prompt, photo_path)
    else:
        # fallback to text-to-image if no photo
        img = generate_flux_text(full_prompt)  # or use another model

    if img:
        img = img.resize((1000, 1414))
        img = overlay_text(img, burden, user_id, level)
        path = f"cert_{user_id}.png"
        img.save(path)
        return path, level
    return None, "Error"
