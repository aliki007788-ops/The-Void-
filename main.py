from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import base64
from cert_gen import generate_royal_certificate

app = FastAPI()

# اجازه دسترسی به وب‌اپلیکیشن (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# دیتابیس قیمت‌ها دقیقاً مطابق فایل ورد شما
PLANS = {
    "kings-luck": {"price": 199, "name": "King's Luck"},
    "divine": {"price": 150, "name": "Divine"},
    "celestial": {"price": 299, "name": "Celestial"},
    "legendary": {"price": 499, "name": "Legendary"}
}

# لیست فرضی برای تابلوی افتخارات (در دیتابیس واقعی ذخیره شود)
winners_db = [
    {"user_id": "882***12", "level": "Legendary"},
    {"user_id": "441***09", "level": "Divine"},
    {"user_id": "773***55", "level": "Luck"},
    {"user_id": "210***88", "level": "Celestial"}
]

@app.post("/create_stars_invoice")
async def create_invoice(request: Request):
    """
    ایجاد فاکتور پرداخت ستاره تلگرام بر اساس پلن انتخابی
    """
    data = await request.json()
    user_id = data.get("u")
    burden = data.get("b")
    plan_key = data.get("type")
    photo_b64 = data.get("p") # عکس ارسالی از وب‌اپلیکیشن
    
    plan_info = PLANS.get(plan_key, PLANS["divine"])
    price = plan_info["price"]

    print(f"User {user_id} requested {plan_key} for {price} stars.")

    # در اینجا متد ایجاد اینویس تلگرام (createInvoiceLink) فراخوانی می‌شود
    # برای مثال یک لینک تستی برمی‌گردانیم:
    invoice_url = f"https://t.me/invoice/test_stars_{price}"
    
    # ذخیره موقت داده‌ها برای مرحله بعد از پرداخت...
    # (در دنیای واقعی اینجا باید در دیتابیس وضعیت PENDING ذخیره شود)
    
    return {"url": invoice_url}

@app.get("/api/hall-of-fame")
async def get_hall():
    """
    ارائه لیست ۱۰ صعودکننده آخر برای صفحه اول
    """
    return {"winners": winners_db[-10:]}

@app.post("/payment_success_webhook")
async def on_payment_success(user_id: str, plan: str, burden: str, photo_data: str):
    """
    این تابع پس از تایید پرداخت توسط تلگرام اجرا می‌شود
    """
    # تبدیل عکس از Base64 به بایت
    user_img_bytes = base64.b64decode(photo_data.split(",")[1]) if photo_data else None
    
    # تولید گواهینامه نهایی
    cert_image = generate_royal_certificate(
        user_img_bytes, 
        burden, 
        PLANS[plan]["name"], 
        user_id
    )
    
    # ارسال عکس نهایی به بات تلگرام برای کاربر
    # requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", ...)
    
    return {"status": "Ascension Complete"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
