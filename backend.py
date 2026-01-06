from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
import base64
import io
from PIL import Image
import json
import os
from datetime import datetime, timedelta
import sqlite3

app = Flask(__name__)
CORS(app)  # اجازه دسترسی از frontend

# توکن Hugging Face شما - اینجا قرار بدید
HF_TOKEN = "YOUR_HUGGINGFACE_TOKEN_HERE"

# دیتابیس ساده برای محدودیت روزانه
def init_db():
    conn = sqlite3.connect('void.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, 
                  last_free_mint DATE,
                  free_mints_today INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "active", "service": "THE VOID ASCENSION"})

@app.route('/api/generate-free', methods=['POST'])
def generate_free():
    """
    تولید NFT رایگان - بدون عکس کاربر
    فقط بر اساس متن burden
    """
    try:
        data = request.json
        user_id = data.get('user_id', 0)
        burden = data.get('burden', 'Unknown Burden')
        
        # چک محدودیت روزانه
        conn = sqlite3.connect('void.db')
        c = conn.cursor()
        
        today = datetime.now().date()
        c.execute('SELECT last_free_mint, free_mints_today FROM users WHERE user_id = ?', (user_id,))
        user_data = c.fetchone()
        
        if user_data:
            last_date, count = user_data
            if last_date and datetime.strptime(last_date, '%Y-%m-%d').date() == today:
                if count >= 2:
                    conn.close()
                    return jsonify({"error": "Daily limit reached"}), 400
                new_count = count + 1
                c.execute('UPDATE users SET free_mints_today = ? WHERE user_id = ?', (new_count, user_id))
            else:
                c.execute('UPDATE users SET last_free_mint = ?, free_mints_today = 1 WHERE user_id = ?', 
                         (today.strftime('%Y-%m-%d'), user_id))
        else:
            c.execute('INSERT INTO users (user_id, last_free_mint, free_mints_today) VALUES (?, ?, 1)',
                     (user_id, today.strftime('%Y-%m-%d')))
        
        conn.commit()
        conn.close()
        
        # پرامپت‌های زیبا برای Eternal (رایگان)
        free_prompts = [
            f"masterpiece cinematic portrait, cosmic void background, golden particles swirling around {burden} concept, divine light rays, ultra-detailed 8K, trending on artstation",
            f"epic fantasy artwork, {burden} ascension to void, dark cosmic energy, ethereal glow, intricate details, digital painting",
            f"mythological god portrait, {burden} embodiment, celestial realm, heavenly light, baroque style, hyperrealistic",
            f"dark fantasy illustration, {burden} ritual, occult symbols floating, mysterious atmosphere, cinematic lighting",
            f"renaissance painting style, {burden} apotheosis, golden halo, divine intervention, oil painting texture"
        ]
        
        import random
        prompt = random.choice(free_prompts)
        
        # فراخوانی Hugging Face API
        headers = {
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "num_inference_steps": 35,
                "guidance_scale": 7.5,
                "width": 1024,
                "height": 1024,
                "negative_prompt": "ugly, deformed, blurry, low quality, watermark"
            }
        }
        
        response = requests.post(
            "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            # ذخیره عکس
            img = Image.open(io.BytesIO(response.content))
            
            # تبدیل به base64 برای ارسال به frontend
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            return jsonify({
                "success": True,
                "image": f"data:image/png;base64,{img_str}",
                "prompt": prompt,
                "remaining_free": 2 - new_count if 'new_count' in locals() else 1
            })
        else:
            return jsonify({"error": f"Hugging Face API error: {response.text}"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate-paid', methods=['POST'])
def generate_paid():
    """
    تولید NFT پولی - با عکس کاربر (img2img)
    """
    try:
        data = request.json
        user_id = data.get('user_id', 0)
        burden = data.get('burden', 'Unknown Burden')
        plan = data.get('plan', 'divine')
        image_base64 = data.get('image')  # عکس کاربر base64
        
        if not image_base64:
            return jsonify({"error": "User image required"}), 400
        
        # حذف header data:image اگر وجود دارد
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        
        # پرامپت‌های لوکس بر اساس سطح پلن
        plan_prompts = {
            'divine': [
                f"luxurious royal portrait of person, golden crown, divine light rays, {burden} concept, masterpiece cinematic lighting, hyper-detailed skin, intricate jewelry",
                f"baroque style portrait, velvet robes, pearl necklace, {burden} theme, oil painting texture, rich colors"
            ],
            'celestial': [
                f"celestial nebula portrait, cosmic jewels floating around person, eternal glow aura, {burden} concept, 8K ultra-detailed, space background",
                f"starry night portrait, galaxy in background, ethereal light, {burden} embodiment, fantasy digital art"
            ],
            'legendary': [
                f"legendary emperor portrait, void throne behind person, ultimate power aura, {burden} concept, hyper-realistic masterpiece, cinematic epic",
                f"mythological god-king portrait, lightning effects, cosmic armor, {burden} incarnation, photorealistic"
            ]
        }
        
        import random
        prompts = plan_prompts.get(plan, plan_prompts['divine'])
        prompt = random.choice(prompts)
        
        # آماده‌سازی برای img2img
        headers = {
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": {
                "image": image_base64,
                "prompt": prompt,
                "strength": 0.35,  # قدرت کم برای حفظ چهره کاربر
                "guidance_scale": 7.0,
                "num_inference_steps": 40,
                "negative_prompt": "ugly, deformed, blurry, distorted face, extra limbs, bad anatomy"
            }
        }
        
        # استفاده از مدل img2img
        response = requests.post(
            "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            
            # تبدیل به base64
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            return jsonify({
                "success": True,
                "image": f"data:image/png;base64,{img_str}",
                "prompt": prompt,
                "plan": plan
            })
        else:
            return jsonify({"error": f"Hugging Face API error: {response.text}"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/check-limit', methods=['POST'])
def check_limit():
    """چک کردن محدودیت روزانه کاربر"""
    try:
        data = request.json
        user_id = data.get('user_id', 0)
        
        conn = sqlite3.connect('void.db')
        c = conn.cursor()
        
        today = datetime.now().date()
        c.execute('SELECT last_free_mint, free_mints_today FROM users WHERE user_id = ?', (user_id,))
        user_data = c.fetchone()
        
        remaining = 2
        if user_data:
            last_date, count = user_data
            if last_date and datetime.strptime(last_date, '%Y-%m-%d').date() == today:
                remaining = 2 - count
                if remaining < 0:
                    remaining = 0
        
        conn.close()
        
        return jsonify({
            "user_id": user_id,
            "remaining_free": remaining,
            "reset_time": "00:00 UTC"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
