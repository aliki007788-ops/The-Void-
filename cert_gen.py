import os, requests, base64, time, io, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

HF_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
HF_TOKEN = os.getenv("HF_TOKEN")

PROMPTS = {
    "vagabond": [
        "luxurious dark royal certificate with ornate golden arabesque frame, intricate jewels and diamonds, cosmic nebula background, sacred geometry mandala, elegant ancient gold font, ultra-detailed masterpiece cinematic lighting",
        "imperial Persian miniature style certificate, golden illumination with arabesque patterns, cosmic void with stars, divine light rays, luxurious jewels, masterpiece",
        "Byzantine golden icon certificate with halo and sacred geometry, dark cosmic background, intricate gold filigree, eternal glow, ultra-detailed",
        "Fabergé egg luxury certificate, golden enamel with plasma jewels, cosmic void, divine aura, intricate details, 8K masterpiece",
        # ... (در اینجا ۵۰ پرامپت سطح ۱ شما قرار می‌گیرد)
    ],
    "divine": [
        "absolute masterpiece divine portrait in Fabergé imperial egg style, golden enamel jewels plasma crown halo, cosmic void sacred geometry, ultra-detailed 8K cinematic lighting",
        "Byzantine holy icon divine portrait with golden halo and sacred mandala jewels, eternal light rays, masterpiece",
        "Persian shah miniature royal portrait with intricate gold illumination, cosmic nebula jewels, divine aura",
        # ... (در اینجا ۴۰ پرامپت سطح ۲ شما قرار می‌گیرد)
    ],
    "celestial": [
        "celestial phoenix rebirth wings portrait with golden eternal flame and cosmic fire divine aura",
        "sacred geometry infinite flower of life golden portrait with cosmic harmony mandala",
        "sovereign imperial diamond plasma crown portrait with eternal sovereign glow",
        # ... (در اینجا ۳۰ پرامپت سطح ۳ شما قرار می‌گیرد)
    ],
    "legendary": [
        "legendary void emperor infinite darkness throne with cosmic plasma jewels eternal crown",
        "ultimate divine phoenix eternal rebirth with golden wings cosmic fire halo masterpiece",
        "legendary sacred geometry flower of life infinite golden mandala with divine light rays",
        # ... (در اینجا ۳۰ پرامپت سطح ۴ شما قرار می‌گیرد)
    ]
}

def query_ai(image_b64, rank, burden):
    prompt_list = PROMPTS.get(rank, PROMPTS["vagabond"])
    base_prompt = random.choice(prompt_list)
    full_prompt = f"{base_prompt}, depicting '{burden}', highly detailed, regal colors"
    
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": full_prompt}
    if image_b64:
        payload["image"] = image_b64.split(",")[-1]

    response = requests.post(HF_API_URL, headers=headers, json=payload)
    return response.content

def create_certificate(user_id, burden, photo_b64=None, rank='vagabond'):
    # ۱. تولید تصویر با هوش مصنوعی
    ai_image_data = query_ai(photo_b64, rank, burden)
    img = Image.open(io.BytesIO(ai_image_data)).convert('RGB')
    img = img.resize((1024, 1024))
    draw = ImageDraw.Draw(img)

    # ۲. اضافه کردن لایه‌های امنیتی و DNA (بخش ۱۴)
    dna_code = f"VOID-DNA-{user_id}-{int(time.time())}"
    try: font = ImageFont.truetype("arial.ttf", 40)
    except: font = ImageFont.load_default()
    
    # درج DNA در پایین تصویر به صورت ظریف
    draw.text((512, 980), dna_code, fill=(255,215,0,100), font=font, anchor="mm")
    
    # ۳. درج متن فداکاری (Burden)
    draw.text((512, 850), burden.upper(), fill="white", font=font, anchor="mm")

    output_path = f"static/outputs/void_{user_id}.png"
    img.save(output_path)
    return output_path
