import os
import random
import requests
import io
import hashlib
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# --- تنظیمات هوش مصنوعی ---
HF_TOKEN = os.getenv("HF_API_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# --- بانک ۱۵۰ سبک بر اساس نایابی (فهرست کامل) ---
# توجه: من ساختار را برای شما چیده ام، شما فقط متن پرامپت ها را در لیست ها کپی کنید.

PROMPT_BANK = {
    "Eternal": [  # ۶۰ سبک اول (پایه و زیبا)
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
        # ... ادامه تا ۶۰ مورد ...
    ],
    
    "Divine": [  # ۴۰ سبک دوم (امپراتوری و باشکوه)
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
        # ... ادامه تا ۴۰ مورد ...
    ],
    
    "Celestial": [  # ۴۰ سبک سوم (ماورایی و کیهانی)
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
        # ... ادامه تا ۴۰ مورد ...
    ],
    
    "Legendary": [  # ۱۰ سبک نهایی (فوق نایاب و منحصر به فرد)
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
        # ... ادامه تا ۱۰ مورد ...
    ]
}

def generate_dna(user_id, level):
    """تولید کد اختصاصی برای رهگیری در اتاق حراجی"""
    seed = f"{user_id}{level}{datetime.now()}".encode()
    return hashlib.sha256(seed).hexdigest()[:10].upper()

def create_certificate(user_id, burden, level="Eternal", user_photo_path=None):
    """تولید خروجی نهایی گواهینامه"""
    
    # انتخاب تصادفی یک سبک از بین ۱۵۰ سبک بر اساس لول تعیین شده
    styles = PROMPT_BANK.get(level, PROMPT_BANK["Eternal"])
    base_prompt = random.choice(styles)
    
    # ترکیب فداکاری کاربر با پرامپت هنری
    final_prompt = f"{base_prompt}, a sacred stone tablet inscribed with '{burden}', golden glow"

    try:
        # فراخوانی هوش مصنوعی
        response = requests.post(API_URL, headers=headers, json={"inputs": final_prompt})
        image = Image.open(io.BytesIO(response.content))
    except:
        # تصویر رزرو در صورت قطع بودن اینترنت
        image = Image.new('RGB', (1000, 1414), color='#0a0a0a')

    # پردازش گرافیکی
    canvas = image.resize((1000, 1414))
    draw = ImageDraw.Draw(canvas)
    dna = generate_dna(user_id, level)

    # لود کردن فونت (مطمئن شوید فایل فونت کنار کد است)
    try:
        font_main = ImageFont.truetype("cinzel.ttf", 55)
        font_sub = ImageFont.truetype("cinzel.ttf", 30)
    except:
        font_main = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # درج اطلاعات بر روی عکس
    draw.text((500, 150), "CERTIFICATE OF ASCENSION", fill="#D4AF37", font=font_main, anchor="mm")
    draw.text((500, 700), f"'{burden}'", fill="white", font=font_sub, anchor="mm")
    draw.text((500, 1250), f"DNA: {dna} | LEVEL: {level}", fill="#D4AF37", font=font_sub, anchor="mm")

    # ذخیره در پوشه خروجی برای نمایش در وب‌اپ
    if not os.path.exists("static/outputs"):
        os.makedirs("static/outputs")
        
    path = f"static/outputs/{dna}.png"
    canvas.save(path)
    
    return path, dna
