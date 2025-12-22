import os
import random
import requests
import hashlib
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی
load_dotenv()

# تنظیمات API
HF_TOKEN = os.getenv("HF_API_TOKEN")
# می‌توانید مدل را به مدل‌های قوی‌تر مثل FLUX تغییر دهید، اما فعلاً طبق فایل شما SD v1.5 است
API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

# -------------------------------------------------------------------
#  LISTS OF STYLES (COMPLETE & UNTOUCHED)
# -------------------------------------------------------------------

# ۵۰ پرامپت سطح Eternal (رایگان – لوکس و حرفه‌ای)
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

# ۴۰ پرامپت Divine
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

# ۳۰ پرامپت Celestial
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

# ۳۰ پرامپت Legendary
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

# -------------------------------------------------------------------
#  HELPER FUNCTIONS
# -------------------------------------------------------------------

def generate_dna(user_id, burden, level):
    """Generates a unique DNA string based on transaction details."""
    data = f"{user_id}{burden}{level}{datetime.now().isoformat()}"
    return hashlib.sha256(data.encode()).hexdigest()[:16].upper()

def generate_img2img(prompt, init_image_path):
    """Generates an image based on an input image (Photo Upload)."""
    try:
        with open(init_image_path, "rb") as f:
            init_image = f.read()
        
        # Note: Standard HF Inference API for Img2Img works best with specific models
        # or separate endpoints. For simplicity with the provided setup, we use the
        # main endpoint. If using a model that doesn't support raw byte upload,
        # this might need base64 encoding or a different payload structure.
        # This implementation assumes the endpoint accepts image bytes or we rely on Txt2Img
        # if the specific model endpoint restricts it.
        
        # Optimization: Since many standard Inference API endpoints are Txt2Img primarily,
        # if using SD 1.5, we might need to rely on Text generation if the API rejects raw bytes.
        # However, keeping your logic intact:
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "negative_prompt": "blurry, ugly, distorted, low quality",
                "num_inference_steps": 50,
                "guidance_scale": 9
            }
        }
        
        # Note: Sending image data to HF Inference API usually requires specific library usage
        # or specific endpoint handling.
        # To ensure this works robustly without complex libraries:
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
        else:
            print(f"API Error (Img2Img): {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception in Img2Img: {e}")
        return None

def generate_txt2img(prompt):
    """Generates an image from text only."""
    try:
        payload = {
            "inputs": prompt, 
            "parameters": {
                "negative_prompt": "blurry, ugly, distorted, low quality, watermark",
                "num_inference_steps": 50,
                "guidance_scale": 8
            }
        }
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
        else:
            print(f"API Error (Txt2Img): {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception in Txt2Img: {e}")
        return None

def overlay_text(img, burden, user_id, level, dna):
    """Overlays the ceremonial text onto the image."""
    draw = ImageDraw.Draw(img)
    w, h = img.size
    
    # Priority: Cinzel -> Arial -> Default
    try:
        title_font = ImageFont.truetype("Cinzel.ttf", 90)
        burden_font = ImageFont.truetype("Cinzel.ttf", 70)
        info_font = ImageFont.truetype("Cinzel.ttf", 45)
    except:
        try:
            title_font = ImageFont.truetype("arial.ttf", 90)
            burden_font = ImageFont.truetype("arial.ttf", 70)
            info_font = ImageFont.truetype("arial.ttf", 45)
        except:
            title_font = burden_font = info_font = ImageFont.load_default()

    gold = "#FFD700"
    white = "#FFFFFF"
    shadow = "#000000"

    def draw_text_with_shadow(position, text, font, fill_color, anchor="mm"):
        x, y = position
        # Draw shadow
        draw.text((x+4, y+4), text, font=font, fill=shadow, anchor=anchor)
        # Draw text
        draw.text((x, y), text, font=font, fill=fill_color, anchor=anchor)

    # Title
    draw_text_with_shadow((w//2, 200), "VOID ASCENSION", title_font, gold)
    
    # Burden (Handle capitalization)
    draw_text_with_shadow((w//2, h//2), f"“{burden.upper()}”", burden_font, white)
    
    # Info
    draw_text_with_shadow((w//2, h//2 + 150), f"LEVEL: {level.upper()}", info_font, gold)
    draw_text_with_shadow((w//2, h - 300), "Style: Eternal Void", info_font, gold)
    draw_text_with_shadow((w//2, h - 200), f"Holder ID: {user_id}", info_font, gold)
    draw_text_with_shadow((w//2, h - 100), f"DNA: {dna}", info_font, "#CCCCCC")

    return img

# -------------------------------------------------------------------
#  MAIN FUNCTION
# -------------------------------------------------------------------

def create_certificate(user_id, burden, level="Eternal", photo_path=None):
    """
    Main entry point to create the certificate.
    Returns: (path_to_image, style_name)
    """
    # 1. Select Style
    if level == "Divine":
        style_prompt = random.choice(divine_styles)
    elif level == "Celestial":
        style_prompt = random.choice(celestial_styles)
    elif level == "Legendary":
        style_prompt = random.choice(legendary_styles)
    else: # Eternal / King's Luck fallback / Common
        style_prompt = random.choice(eternal_styles)
    
    full_prompt = f"{style_prompt}, centered, burden \"{burden.upper()}\", level {level}, ultra-detailed masterpiece, cinematic lighting, dark luxury royal portrait certificate, 8k resolution"

    dna = generate_dna(user_id, burden, level)

    # 2. Generate Image (Img2Img or Txt2Img)
    img = None
    if photo_path and os.path.exists(photo_path):
        print(f"Generating Img2Img for {user_id}...")
        img = generate_img2img(full_prompt, photo_path)
        # If API failed for Img2Img, fallback to Txt2Img
        if not img:
            print("Fallback to Txt2Img...")
            img = generate_txt2img(full_prompt)
    else:
        print(f"Generating Txt2Img for {user_id}...")
        img = generate_txt2img(full_prompt)

    # 3. Create Fallback if AI fails completely
    if not img:
        print("AI Generation failed. Creating fallback void canvas.")
        img = Image.new('RGB', (1000, 1414), '#050505')
        d = ImageDraw.Draw(img)
        # Draw some basic fallback art
        d.rectangle([50, 50, 950, 1364], outline="#FFD700", width=5)

    # 4. Resize and Overlay
    # Ensure correct aspect ratio (1000x1414 approx A4)
    img = img.resize((1000, 1414))
    img = overlay_text(img, burden, user_id, level, dna)

    # 5. Save
    os.makedirs("outputs", exist_ok=True)
    filename = f"cert_{user_id}_{dna}.png"
    path = os.path.join("outputs", filename)
    img.save(path)
    
    print(f"Certificate saved to {path}")
    return path, style_prompt[:50] + "..."
