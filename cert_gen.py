import os, random, time
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

def create_certificate(user_id, burden, photo_path=None, rank='free'):
    w, h = 1000, 1000  # Square for NFT Marketplaces
    img = Image.new('RGB', (w, h), '#000000')
    draw = ImageDraw.Draw(img)
    
    # 3D Cyber Grids
    for i in range(0, w, 40):
        draw.line((i, 0, i, h), fill="#0a0a0a")
        draw.line((0, i, w, i), fill="#0a0a0a")

    # Image Processing
    if photo_path and os.path.exists(photo_path):
        user_img = Image.open(photo_path).convert('RGB')
        user_img = ImageOps.fit(user_img, (500, 500))
        mask = Image.new('L', (500, 500), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 500, 500), fill=255)
        
        # Color Aura
        aura_color = "#00f2ff" if rank == 'legendary' else "#FFD700" if rank == 'rare' else "#444"
        glow = Image.new('RGBA', (550, 550), (0,0,0,0))
        ImageDraw.Draw(glow).ellipse((0, 0, 550, 550), outline=aura_color, width=20)
        glow = glow.filter(ImageFilter.GaussianBlur(20))
        img.paste(glow, (w//2-275, 125), glow)
        
        img.paste(user_img, (w//2-250, 150), mask)

    # Metadata & Text
    try: font = ImageFont.truetype("arial.ttf", 50)
    except: font = ImageFont.load_default()
    
    draw.text((w//2, 750), burden.upper(), fill="white", font=font, anchor="mm")
    draw.text((w//2, 820), f"RANK: {rank.upper()}", fill="#FFD700", font=font, anchor="mm")
    
    # Unique DNA (for NFT uniqueness)
    dna = f"VOID-{int(time.time())}-{user_id}"
    draw.text((w//2, 950), dna, fill="#222", font=font, anchor="mm")

    output_path = f"static/outputs/cert_{user_id}_{int(time.time())}.png"
    img.save(output_path)
    return output_path
