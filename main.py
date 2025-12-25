import os
import random
import threading
import time
from flask import Flask, request, jsonify, send_from_directory
from telebot import TeleBot, types

# --- تنظیمات اصلی ---
API_TOKEN = 'YOUR_BOT_TOKEN_HERE' 
WEBAPP_URL = 'https://the-void-1.onrender.com'

bot = TeleBot(API_TOKEN)
app = Flask(__name__)

# تنظیم مسیرها
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "static", "outputs")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- پیام خوش‌آمدگویی ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"🔱 **درود بر تو، {user_name.upper()}** 🔱\n\n"
        "به تالار **THE VOID** خوش آمدی. جایی که رنج‌های تو به آثار جاودانه‌ی طلایی تبدیل می‌شوند.\n\n"
        "🏛️ *سرنوشت در انتظار توست...*"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔱 ENTER THE VOID 🔱", web_app=types.WebAppInfo(WEBAPP_URL)))
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

# --- API برای پنل HTML ---
@app.route('/api/gallery/<int:user_id>', methods=['GET'])
def get_gallery(user_id):
    user_images = []
    prefix = f"user_{user_id}_"
    if os.path.exists(OUTPUT_DIR):
        for filename in os.listdir(OUTPUT_DIR):
            if filename.startswith(prefix):
                user_images.append({
                    "url": f"/static/outputs/{filename}",
                    "dna": filename.split('_')[-1].split('.')[0]
                })
    user_images.sort(key=lambda x: x['dna'], reverse=True)
    return jsonify({"images": user_images})

@app.route('/api/mint', methods=['POST'])
def mint_artifact():
    try:
        data = request.json
        user_id = data.get('u')
        burden = data.get('b', 'Unknown Burden')
        plan_type = data.get('p', 'eternal')
        
        artifact_id = random.randint(1000000, 9999999)
        filename = f"user_{user_id}_art_{artifact_id}.jpg"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        # ایجاد فایل دیتای تستی (در آینده تصویر اصلی)
        with open(filepath, "wb") as f:
            f.write(os.urandom(2048))

        # ارسال عکس به بات تلگرام
        with open(filepath, 'rb') as photo:
            caption = f"🔱 **ASCENSION COMPLETE** 🔱\n\n📜 **Burden:** *{burden}*\n🧬 **DNA:** `{artifact_id}`"
            bot.send_photo(user_id, photo, caption=caption, parse_mode="Markdown")
        
        return jsonify({"status": "success", "dna": artifact_id, "url": f"/static/outputs/{filename}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- مسیرهای فایل ---
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/static/outputs/<path:path>')
def serve_static(path):
    return send_from_directory(OUTPUT_DIR, path)

# --- اجرای همزمان ---
def start_polling():
    # حذف هرگونه وب‌هوک قدیمی برای جلوگیری از خطای 404 در لاگ
    bot.remove_webhook()
    time.sleep(1)
    print("Starting Bot Polling...")
    bot.infinity_polling(skip_pending=True)

if __name__ == '__main__':
    # اجرای ربات در ترد جداگانه
    threading.Thread(target=start_polling, daemon=True).start()
    
    # اجرای وب‌سرور بر اساس پورت Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
