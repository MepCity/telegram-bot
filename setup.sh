#!/bin/bash

echo "🤖 Teklif Botu Kurulum Scripti"
echo "================================"
echo ""

# Renk kodları
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Python kontrolü
echo "📦 Python kontrolü..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 bulunamadı!${NC}"
    echo "Lütfen Python 3.10 veya üstünü yükleyin: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✅ Python $PYTHON_VERSION bulundu${NC}"

# Virtual environment oluştur
echo ""
echo "🔧 Sanal ortam oluşturuluyor..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Sanal ortam oluşturuldu${NC}"
else
    echo -e "${YELLOW}⚠️  Sanal ortam zaten mevcut${NC}"
fi

# Virtual environment'ı aktifleştir
echo ""
echo "🔌 Sanal ortam aktifleştiriliyor..."
source venv/bin/activate

# Bağımlılıkları yükle
echo ""
echo "📥 Bağımlılıklar yükleniyor..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

echo -e "${GREEN}✅ Bağımlılıklar yüklendi${NC}"

# Tesseract kontrolü
echo ""
echo "👁️  Tesseract OCR kontrolü..."
if ! command -v tesseract &> /dev/null; then
    echo -e "${YELLOW}⚠️  Tesseract bulunamadı!${NC}"
    echo "PDF okuma için Tesseract gereklidir."
    echo ""
    echo "macOS için:"
    echo "  brew install tesseract"
    echo ""
    echo "Ubuntu/Debian için:"
    echo "  sudo apt-get install tesseract-ocr tesseract-ocr-tur"
    echo ""
else
    TESSERACT_VERSION=$(tesseract --version | head -n1)
    echo -e "${GREEN}✅ $TESSERACT_VERSION bulundu${NC}"
fi

# .env dosyası kontrolü
echo ""
echo "⚙️  Konfigürasyon kontrolü..."
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env dosyası bulunamadı${NC}"
    echo "📝 .env.example dosyasından .env oluşturuluyor..."
    cp .env.example .env
    echo -e "${GREEN}✅ .env dosyası oluşturuldu${NC}"
    echo ""
    echo -e "${RED}ÖNEMLİ: .env dosyasını düzenleyin ve Telegram Bot Token'ı ekleyin!${NC}"
    echo ""
else
    echo -e "${GREEN}✅ .env dosyası mevcut${NC}"
fi

# Dizinleri oluştur
echo ""
echo "📁 Dizinler oluşturuluyor..."
mkdir -p outputs temp
echo -e "${GREEN}✅ Dizinler hazır${NC}"

# Excel template kontrolü
echo ""
echo "📊 Excel template kontrolü..."
if [ ! -f "YTB Teklif.xlsx" ]; then
    echo -e "${RED}❌ YTB Teklif.xlsx bulunamadı!${NC}"
    echo "Lütfen template Excel dosyasını bot klasörüne ekleyin."
else
    echo -e "${GREEN}✅ Template dosyası mevcut${NC}"
fi

# Test
echo ""
echo "🧪 Test ediliyor..."
python3 excel_handler.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Excel handler testi başarılı${NC}"
else
    echo -e "${RED}❌ Test başarısız${NC}"
fi

# Özet
echo ""
echo "================================"
echo -e "${GREEN}🎉 Kurulum tamamlandı!${NC}"
echo ""
echo "Şimdi yapılacaklar:"
echo ""
echo "1️⃣  .env dosyasını düzenleyin:"
echo "   nano .env"
echo ""
echo "2️⃣  Telegram Bot Token ekleyin:"
echo "   @BotFather'dan bot oluşturun ve token'ı alın"
echo ""
echo "3️⃣  Botu başlatın:"
echo "   source venv/bin/activate"
echo "   python bot.py"
echo ""
echo "📖 Detaylı bilgi için README.md dosyasını okuyun"
echo ""
