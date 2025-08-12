# استخدم صورة بايثون أساسية
FROM python:3.9-slim-buster

# قم بتعيين دليل العمل داخل الحاوية
WORKDIR /app

# انسخ ملف المتطلبات وقم بتثبيت التبعيات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# إنشاء مجلد لقاعدة البيانات والتأكد من أذوناته
# هذا يضمن أن مجلد 'instance' موجود وقابل للكتابة داخل الحاوية
# RUN mkdir -p /app/instance && chmod 777 /app/instance

# انسخ بقية ملفات التطبيق (بما في ذلك app.py و templates والمجلدات الأخرى)
COPY . .

# كشف المنفذ الذي يستمع عليه التطبيق
EXPOSE 5000

# الأمر لتشغيل التطبيق عند بدء تشغيل الحاوية
CMD ["python", "app.py"]
