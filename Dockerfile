# Railway Dockerfile - LibreOffice ile Python bot
FROM python:3.11-slim

# Sistem paketlerini güncelle
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    tesseract-ocr \
    tesseract-ocr-tur \
    fonts-liberation \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizini
WORKDIR /app

# Python bağımlılıklarını kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyalarını kopyala
COPY . .

# Temp ve outputs klasörlerini oluştur
RUN mkdir -p temp outputs

# Botu çalıştır
CMD ["python3", "bot.py"]
