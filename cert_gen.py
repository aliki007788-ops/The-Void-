import os
import random
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io

HF_TOKEN = os.getenv("HF_API_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

eternal_styles = [  # ۵۰ سبک رایگان
    "luxurious dark royal certificate, golden ornate frame with diamonds, cosmic nebula background, sacred geometry mandala, elegant ancient gold font, masterpiece",
    "imperial Byzantine icon style certificate, golden halo and intricate sacred geometry, dark void with stars, cinematic lighting",
    # ... (۵۰ تا کامل – در کد واقعی همه اضافه می‌شن)
]

premium_styles = [  # ۱۰۰ سبک پولی
    "absolute masterpiece divine portrait in Fabergé imperial egg style, golden enamel jewels plasma crown halo, cosmic void, sacred geometry, ultra-detailed 8K",
    "Byzantine holy icon divine portrait with golden halo and sacred mandala jewels, eternal light rays, masterpiece",
    # ... (۱۰۰ تا کامل)
]

def generate_flux_image(prompt):
    payload = {"inputs": prompt, "parameters": {"num_inference_steps": 4}}
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

    draw.text((w//2, 200), "VOID ASCENSION", fill="#FFD700", font=title_font, anchor="mm", stroke_width=5, stroke_fill="#000")
    draw.text((w//2, h//2), f"“{burden.upper()}”", fill="#FFFFFF", font=burden_font, anchor="mm", stroke_width=4, stroke_fill="#000")
    draw.text((w//2, h//2 + 150), f"LEVEL: {level}", fill="#FFD700", font=info_font, anchor="mm")
    draw.text((w//2, h - 300), "Style: Custom Void", fill="#FFD700", font=info_font, anchor="mm")
    draw.text((w//2, h - 200), f"Holder ID: {user_id}", fill="#FFD700", font=info_font, anchor="mm")
    draw.text((w//2, h - 100), "2025.VO-ID", fill="#888888", font=info_font, anchor="mm")
    return img

def create_certificate(user_id, burden, level="Eternal", photo_path=None):
    if level == "Eternal":
        prompt_base = random.choice(eternal_styles)
    else:
        prompt_base = random.choice(premium_styles)
    
    prompt = f"{prompt_base}, burden \"{burden.upper()}\", level {level}, ultra-detailed masterpiece"
    
    img = generate_flux_image(prompt)
    if img:
        img = img.resize((1000, 1414))
        img = overlay_text(img, burden, user_id, level)
        path = f"cert_{user_id}.png"
        img.save(path)
        return path, level
    return None, "Error"
