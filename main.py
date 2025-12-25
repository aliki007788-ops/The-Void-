import os
import random
import logging
from flask import Flask, request, jsonify, send_from_directory
from telebot import TeleBot, types

# تنظیمات پایه
API_TOKEN = 'YOUR_BOT_TOKEN_HERE' # توکن ربات خود را اینجا بگذارید
bot = TeleBot(API_TOKEN)
app = Flask(__name__)

# ایجاد پوشه برای ذخیره تصاویر اگر وجود نداشته باشد
OUTPUT_DIR = "static/outputs"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# --- بخش ربات تلگرام (پیام خوش‌آمدگویی) ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"🔱 **WELCOME TO THE VOID, {user_name.upper()}** 🔱\n\n"
        "You have reached the edge of existence. Here, your burdens "
        "are transformed into eternal golden artifacts.\n\n"
        "✨ **Step 1:** Open the App below.\n"
        "✨ **Step 2:** Name your sacrifice.\n"
        "✨ **Step 3:** Ascend to your final form.\n\n"
        "*Fortune favors the bold.*"
    )
    
    # دکمه باز کردن اپلیکیشن
    markup = types.InlineKeyboardMarkup()
    web_app = types.WebAppInfo("https://your-domain.com") # آدرس سایت خود را اینجا بگذارید
    btn = types.InlineKeyboardButton("🔱 ENTER THE VOID 🔱", web_app=web_app)
    markup.add(btn)
    
    bot.send_message(
        message.chat.id, 
        welcome_text, 
        parse_mode="Markdown", 
        reply_markup=markup
    )

# --- بخش API برای اتصال به HTML ---

# ۱. دریافت تصاویر گالری برای هر کاربر
@app.route('/api/gallery/<int:user_id>', methods=['GET'])
def get_gallery(user_id):
    # در دنیای واقعی اینجا باید از دیتابیس بخونید، اینجا ما فایل‌ها رو چک می‌کنیم
    user_images = []
    prefix = f"user_{user_id}_"
    
    if os.path.exists(OUTPUT_DIR):
        for filename in os.listdir(OUTPUT_DIR):
            if filename.startswith(prefix):
                user_images.append({
                    "url": f"/static/outputs/{filename}",
                    "dna": filename.split('_')[-1].split('.')[0]
                })
    
    return jsonify({"images": user_images[::-1]}) # نمایش جدیدترین‌ها در ابتدا

# ۲. عملیات Mint (تولید تصویر مصنوعی)
@app.route('/api/mint', methods=['POST'])
def mint_artifact():
    data = request.json
    user_id = data.get('u')
    burden = data.get('b')
    plan_type = data.get('type')
    
    # تولید یک آیدی رندوم برای تصویر (در آینده اینجا هوش مصنوعی وصل می‌شود)
    artifact_id = random.randint(100000, 999999)
    filename = f"user_{user_id}_art_{artifact_id}.jpg"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    # شبیه‌سازی تولید تصویر (در اینجا یک تصویر تست کپی می‌شود یا ساخته می‌شود)
    # برای تست، ما یک فایل خالی یا کپی می‌سازیم
    with open(filepath, "wb") as f:
        # در حالت واقعی، خروجی مدل هوش مصنوعی اینجا ذخیره می‌شود
        f.write(b"fake_image_data") 

    # اطلاع‌رسانی به کاربر در تلگرام
    bot.send_message(
        user_id, 
        f"🔱 **ASCENSION COMPLETE** 🔱\n\nYour burden: *{burden}*\n"
        f"Plan: {plan_type.upper()}\n"
        f"DNA: `{artifact_id}`\n\n"
        "Check your Gallery in the App!"
    )
    
    return jsonify({"status": "success", "dna": artifact_id})

# سرو کردن فایل‌های استاتیک (تصاویر)
@app.route('/static/outputs/<path:path>')
def send_outputs(path):
    return send_from_directory(OUTPUT_DIR, path)

# سرو کردن فایل اصلی HTML
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    # اجرای همزمان ربات و وب سرور
    import threading
    threading.Thread(target=lambda: bot.infinity_polling()).start()
    app.run(host='0.0.0.0', port=5000)
