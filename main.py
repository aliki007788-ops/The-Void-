import os
import random
import threading
from flask import Flask, request, jsonify, send_from_directory
from telebot import TeleBot, types

# --- تنظیمات اولیه ---
# توکن ربات خود را که از BotFather گرفته‌اید اینجا قرار دهید
API_TOKEN = 'YOUR_BOT_TOKEN_HERE' 
# آدرس دامین یا آدرس سرور (مثلاً https://void-app.onrender.com) را اینجا بگذارید
WEBAPP_URL = 'https://your-domain.com'

bot = TeleBot(API_TOKEN)
app = Flask(__name__)

# ایجاد مسیرهای لازم برای ذخیره تصاویر
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "static", "outputs")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- بخش ربات تلگرام (پیام خوش‌آمدگویی) ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    
    # متن خوش‌آمدگویی متناسب با استایل THE VOID
    welcome_text = (
        f"🔱 **درود بر تو، {user_name.upper()}** 🔱\n\n"
        "به قلمرو **THE VOID** خوش آمدی. جایی که رنج‌های تو به آثار جاودانه‌ی طلایی تبدیل می‌شوند.\n\n"
        "✨ **گام اول:** بر روی دکمه زیر کلیک کن تا وارد اپلیکیشن شوی.\n"
        "✨ **گام دوم:** نام بار سنگین یا رنج خود را بنویس.\n"
        "✨ **گام سوم:** قربانی خود را تقدیم کن و تصویر طلایی‌ات را دریافت کن.\n\n"
        "🏛️ *سرنوشت در انتظار توست...*"
    )
    
    # ساخت دکمه شیشه‌ای برای باز کردن WebApp
    markup = types.InlineKeyboardMarkup()
    web_app_info = types.WebAppInfo(WEBAPP_URL)
    enter_btn = types.InlineKeyboardButton("🔱 ENTER THE VOID 🔱", web_app=web_app_info)
    markup.add(enter_btn)
    
    # ارسال پیام همراه با تصویر پس‌زمینه (اختیاری) یا فقط متن
    bot.send_message(
        message.chat.id, 
        welcome_text, 
        parse_mode="Markdown", 
        reply_markup=markup
    )

# --- بخش API برای هماهنگی با فایل HTML شما ---

# ۱. مسیر دریافت تصاویر گالری برای نمایش در اپلیکیشن
@app.route('/api/gallery/<int:user_id>', methods=['GET'])
def get_gallery(user_id):
    user_images = []
    prefix = f"user_{user_id}_"
    
    try:
        if os.path.exists(OUTPUT_DIR):
            files = os.listdir(OUTPUT_DIR)
            # فیلتر کردن فایل‌های مربوط به این کاربر خاص
            for filename in files:
                if filename.startswith(prefix):
                    user_images.append({
                        "url": f"/static/outputs/{filename}",
                        "dna": filename.split('_')[-1].split('.')[0]
                    })
        
        # مرتب‌سازی: نمایش جدیدترین تصاویر در ابتدای لیست
        user_images.sort(key=lambda x: x['dna'], reverse=True)
        return jsonify({"images": user_images})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ۲. مسیر عملیات MINT و تولید تصویر
@app.route('/api/mint', methods=['POST'])
def mint_artifact():
    try:
        data = request.json
        user_id = data.get('u')
        burden = data.get('b', 'Unknown Burden')
        plan_type = data.get('p', 'eternal') # نوع پلن انتخابی کاربر
        
        # تولید یک شناسه منحصر به فرد (DNA) برای تصویر
        artifact_id = random.randint(1000000, 9999999)
        filename = f"user_{user_id}_art_{artifact_id}.jpg"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        # --- بخش تولید تصویر ---
        # در اینجا منطق تولید تصویر یا کپی کردن یک تصویر پیش‌فرض قرار می‌گیرد.
        # برای تست، ما یک تصویر ساده می‌سازیم (در نسخه واقعی مدل هوش مصنوعی اینجا فراخوانی می‌شود)
        # به عنوان مثال فعلاً یک فایل متنی را با پسوند jpg ذخیره می‌کنیم تا خطا ندهد:
        with open(filepath, "wb") as f:
            # شبیه‌سازی دیتای تصویر (جایگزین با خروجی هوش مصنوعی)
            f.write(os.urandom(1024)) 

        # --- ارسال همزمان به تلگرام کاربر ---
        # ارسال پیام تایید همراه با عکس ساخته شده به چت خصوصی کاربر
        with open(filepath, 'rb') as photo:
            caption_text = (
                f"🔱 **ASCENSION COMPLETE** 🔱\n\n"
                f"👤 **User:** `{user_id}`\n"
                f"📦 **Plan:** {plan_type.upper()}\n"
                f"📜 **Burden:** *{burden}*\n"
                f"🧬 **DNA:** `{artifact_id}`\n\n"
                f"آرتیفکت شما با موفقیت در تالار جاودانگی ثبت شد."
            )
            bot.send_photo(
                user_id, 
                photo, 
                caption=caption_text, 
                parse_mode="Markdown"
            )
        
        return jsonify({
            "status": "success", 
            "dna": artifact_id, 
            "url": f"/static/outputs/{filename}"
        })
    
    except Exception as e:
        print(f"Error in minting: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# مسیرهای سرو کردن فایل‌ها
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/static/outputs/<path:path>')
def serve_static(path):
    return send_from_directory(OUTPUT_DIR, path)

# --- اجرای همزمان ربات و وب‌سرور ---
def run_bot():
    print("Bot is running...")
    bot.infinity_polling()

if __name__ == '__main__':
    # اجرای ربات در یک رشته (Thread) جداگانه برای جلوگیری از تداخل با Flask
    threading.Thread(target=run_bot, daemon=True).start()
    
    # اجرای وب‌سرور Flask
    # برای محیط تست از port 5000 استفاده می‌شود
    app.run(host='0.0.0.0', port=5000, debug=False)
