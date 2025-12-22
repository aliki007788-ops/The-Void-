import os, requests, base64, time, io
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

# تنظیمات Hugging Face برای Stable Diffusion img2img
HF_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
HF_TOKEN = os.getenv("HF_TOKEN") # توکن خود را در رندر تنظیم کنید

def query_stable_diffusion(image_base64, prompt):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    # تبدیل تصویر به فرمت مورد نیاز API
    payload = {
        "inputs": prompt,
        "image": image_base64.split(",")[-1], # حذف پیشوند data:image...
        "parameters": {"strength": 0.65, "num_inference_steps": 30}
    }
    response = requests.post(HF_API_URL, headers=headers, json=payload)
    return response.content

def create_certificate(user_id, burden, photo_base64=None, rank='free'):
    w, h = 1024, 1024
    img = Image.new('RGB', (w, h), '#000000')
    draw = ImageDraw.Draw(img)

    # پردازش تصویر با Stable Diffusion در صورت آپلود
    final_soul_img = None
    if photo_base64 and rank != 'free':
        try:
            ai_data = query_stable_diffusion(photo_base64, f"A divine mystical cosmic version of this person, {burden}, cinematic lighting, gold and cyan aura, 8k resolution")
            final_soul_img = Image.open(io.BytesIO(ai_data)).convert('RGB')
        except:
            # Fallback در صورت خطای API
            final_soul_img = Image.open(io.BytesIO(base64.b64decode(photo_base64.split(",")[-1]))).convert('RGB')
    
    # طراحی قاب گواهی
    if final_soul_img:
        final_soul_img = ImageOps.fit(final_soul_img, (600, 600))
        mask = Image.new('L', (600, 600), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 600, 600), fill=255)
        
        # افکت درخشش فیروزه‌ای/طلایی دور تصویر
        aura_color = "#00f2ff" if rank == 'legendary' else "#FFD700"
        glow = Image.new('RGBA', (660, 660), (0,0,0,0))
        ImageDraw.Draw(glow).ellipse((0,0,660,660), outline=aura_color, width=15)
        glow = glow.filter(ImageFilter.GaussianBlur(20))
        img.paste(glow, (w//2-330, 120), glow)
        img.paste(final_soul_img, (w//2-300, 150), mask)

    # متون نهایی
    try: font_b = ImageFont.truetype("arial.ttf", 60); font_s = ImageFont.truetype("arial.ttf", 35)
    except: font_b = font_s = ImageFont.load_default()

    draw.text((w//2, 820), burden.upper(), fill="white", font=font_b, anchor="mm")
    draw.text((w//2, 900), f"LEVEL: {rank.upper()}", fill="#FFD700", font=font_s, anchor="mm")
    
    # DNA Code منحصر‌به‌فرد
    dna = f"VOID-{int(time.time())}-{user_id}"
    draw.text((w//2, 970), dna, fill="#222", font=font_s, anchor="mm")

    path = f"static/outputs/void_{user_id}_{int(time.time())}.png"
    img.save(path)
    return path
