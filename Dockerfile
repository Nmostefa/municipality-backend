# استخدم الصورة الرسمية لـ Python كقاعدة
FROM python:3.9-slim-buster

# عيّن دليل العمل داخل الحاوية
WORKDIR /app

# انسخ ملف المتطلبات إلى الحاوية
COPY requirements.txt .

# ثبّت تبعيات Python
RUN pip install --no-cache-dir -r requirements.txt

# انسخ بقية كود التطبيق إلى الحاوية
COPY . .

# انسخ سكربت البدء واجعله قابلاً للتنفيذ
COPY start.sh .
RUN chmod +x start.sh

# أمر بدء تشغيل التطبيق باستخدام سكربت start.sh
# Render سيقوم تلقائياً بتعيين متغير البيئة PORT
CMD ["./start.sh"]
