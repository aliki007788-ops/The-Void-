import os
import random
import threading
from flask import Flask, request, jsonify, send_from_directory
from telebot import TeleBot, types

# --- تنظیمات اصلی ---
# توکن ربات خود را اینجا قرار دهید
API_TOKEN = 'YOUR_BOT_TOKEN_HERE' 
# آدرس دامین رندر شما
WEBAPP_URL = 'https://the-void-1.onrender.com'

bot = TeleBot(API_TOKEN)
app = Flask(__name__)

# تنظیم مسیرها برای ذخیره تصاویر
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "static", "outputs")

# ایجاد پوشه خروجی اگر وجود نداشته باشد
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- بخش ربات تلگرام (خوش‌آمدگویی) ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"🔱 **درود بر تو، {user_name.upper()}** 🔱\n\n"
        "به تالار **THE VOID** خوش آمدی. جایی که رنج‌های تو به آثار جاودانه‌ی طلایی تبدیل می‌شوند.\n\n"
        "✨ **گام اول:** بر روی دکمه زیر کلیک کن تا وارد اپلیکیشن شوی.\n"
        "✨ **گام دوم:** نام بار سنگین یا رنج خود را بنویس.\n"
        "✨ **گام سوم:** قربانی خود را تقدیم کن و تصویر طلایی‌ات را دریافت کن.\n\n"
        "🏛️ *سرنوشت در انتظار توست...*"
    )
    
    markup = types.InlineKeyboardMarkup()
    web_app_info = types.WebAppInfo(WEBAPP_URL)
    enter_btn = types.InlineKeyboardButton("🔱 ENTER THE VOID 🔱", web_app=web_app_info)
    markup.add(enter_btn)
    
    bot.send_message(
        message.chat.id, 
        welcome_text, 
        parse_mode="Markdown", 
        reply_markup=markup
    )

# --- بخش API هماهنگ با پنل HTML ---

@app.route('/api/gallery/<int:user_id>', methods=['GET'])
def get_gallery(user_id):
    user_images = []
    prefix = f"user_{user_id}_"
    try:
        if os.path.exists(OUTPUT_DIR):
            files = os.listdir(OUTPUT_DIR)
            for filename in files:
                if filename.startswith(prefix):
                    user_images.append({
                        "url": f"/static/outputs/{filename}",
                        "dna": filename.split('_')[-1].split('.')[0]
                    })
        user_images.sort(key=lambda x: x['dna'], reverse=True)
        return jsonify({"images": user_images})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/mint', methods=['POST'])
def mint_artifact():
    try:
        data = request.json
        user_id = data.get('u')
        burden = data.get('b', 'Unknown Burden')
        plan_type = data.get('p', 'eternal')
        
        # تولید شناسه رندوم برای تصویر (DNA)
        artifact_id = random.randint(1000000, 9999999)
        filename = f"user_{user_id}_art_{artifact_id}.jpg"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        # --- شبیه‌سازی تولید تصویر ---
        # در اینجا یک فایل تصویر نمونه ساخته می‌شود
        with open(filepath, "wb") as f:
            f.write(os.urandom(2048)) # دیتای تستی

        # --- ارسال به تلگرام کاربر ---
        with open(filepath, 'rb') as photo:
            caption_text = (
                f"🔱 **ASCENSION COMPLETE** 🔱\n\n"
                f"📜 **Burden:** *{burden}*\n"
                f"🧬 **DNA:** `{artifact_id}`\n\n"
                f"تصویر شما در گالری اپلیکیشن نیز ذخیره شد."
            )
            bot.send_photo(user_id, photo, caption=caption_text, parse_mode="Markdown")
        
        return jsonify({
            "status": "success", 
            "dna": artifact_id, 
            "url": f"/static/outputs/{filename}"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- مدیریت مسیرها ---

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/static/outputs/<path:path>')
def serve_static(path):
    return send_from_directory(OUTPUT_DIR, path)

# --- بخش اجرای اصلی (هماهنگ با Render) ---

if __name__ == '__main__':
    # پاکسازی وب‌هوک‌های قدیمی برای فعال شدن حالت Polling
    bot.remove_webhook()
    
    # اجرای ربات در یک Thread جداگانه
    bot_thread = threading.Thread(target=lambda: bot.infinity_polling(skip_pending=True))
    bot_thread.daemon = True
    bot_thread.start()
    
    # تنظیم پورت Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
