# 🤖 Otomatik Teklif Oluşturma Botu

Danışmanlık şirketleri için otomatik teklif PDF/Excel oluşturan Telegram botu.

## 🎯 Özellikler

- ✅ Telegram üzerinden kolay kullanım
- ✅ Vergi levhası PDF'inden otomatik bilgi çıkarma (OCR)
- ✅ Birden fazla ürün/hizmet ekleme
- ✅ Excel formatında teklif oluşturma
- ✅ Özelleştirilebilir şirket bilgileri
- ✅ Otomatik teklif numarası üretimi

## 📋 Gereksinimler

- Python 3.10+
- Telegram Bot Token (@BotFather'dan alınacak)
- Tesseract OCR (PDF okuma için)

## 🚀 Kurulum

### 1. Repository'yi klonlayın veya indirin

```bash
cd /Users/yasir/Desktop/bot
```

### 2. Sanal ortam oluşturun (önerilen)

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
```

### 3. Bağımlılıkları yükleyin

```bash
pip install -r requirements.txt
```

### 4. Tesseract OCR'ı yükleyin (macOS)

```bash
brew install tesseract
brew install tesseract-lang  # Türkçe dil desteği için
```

Diğer işletim sistemleri için: [Tesseract Kurulum Kılavuzu](https://tesseract-ocr.github.io/tessdoc/Installation.html)

### 5. Telegram Bot oluşturun

1. Telegram'da [@BotFather](https://t.me/botfather) ile konuşun
2. `/newbot` komutunu gönderin
3. Bot adını ve kullanıcı adını belirleyin
4. Aldığınız token'ı kaydedin

### 6. Konfigürasyon

`.env.example` dosyasını `.env` olarak kopyalayın:

```bash
cp .env.example .env
```

`.env` dosyasını düzenleyin ve bilgilerinizi girin:

```bash
TELEGRAM_BOT_TOKEN=sizin_bot_tokeniniz_buraya
COMPANY_NAME=Şirket Adınız
COMPANY_ADDRESS=Şirket Adresiniz
COMPANY_PHONE=Telefon Numaranız
COMPANY_EMAIL=email@sirketiniz.com
```

### 7. Template Excel'i yerleştirin

`yeni.xlsx` dosyasının bot klasöründe olduğundan emin olun. Bu dosya güncel teklif şablonudur (28.10.2025).

> **Not:** Eski şablon `YTB Teklif Yeni.xlsx` artık kullanılmıyor ama yedek olarak saklanıyor.

## 🎮 Kullanım

### Botu Başlatın

```bash
python bot.py
```

### Telegram'dan Kullanım

1. Telegram'da botunuzu bulun ve `/start` yazın
2. `/yeni` komutuyla yeni teklif oluşturmaya başlayın
3. Bot adım adım sizden bilgi isteyecek:
   - 👤 Müşteri/Yetkili adı
   - 📄 Vergi levhası PDF'i
   - 📦 Ürün/Hizmet bilgileri (ad, miktar, fiyat)
   - 📅 Tarih bilgileri
   - 💳 Ödeme şekli
4. Bot teklifi Excel olarak gönderecek

### Komutlar

- `/start` - Botu başlat ve yardım mesajını gör
- `/yeni` - Yeni teklif oluştur
- `/iptal` - Mevcut işlemi iptal et

## 📁 Proje Yapısı

```
bot/
├── bot.py                      # Ana bot dosyası (544 satır)
├── config.py                   # Konfigürasyon ayarları
├── excel_handler.py            # Excel işlemleri
├── pdf_reader.py               # PDF okuma ve OCR (1006 satır)
├── pdf_converter.py            # Excel → PDF dönüştürme
├── document_handler.py         # Word/Excel form doldurma
├── gemini_ocr.py              # Google Gemini Vision AI OCR
├── ai_ocr.py                  # OpenAI GPT-4 Vision (opsiyonel)
├── requirements.txt            # Python bağımlılıkları
├── .env                        # Çevre değişkenleri (GIT'e eklenmez)
├── .env.example                # Örnek çevre değişkenleri
├── yeni.xlsx                   # ⭐ GÜNCEL ŞABLON (28.10.2025)
├── YTB Teklif Yeni.xlsx        # Eski şablon (yedek)
├── outputs/                    # Oluşturulan teklifler
│   └── offer_counter.json      # Teklif numarası sayacı
├── temp/                       # Geçici dosyalar
└── gerek/                      # Ek belgeler (yetkilendirme formları)
    ├── Yetkilendirme Tahattütnamesi.docx
    └── Kullanıcı Yetkilendirme Formu.xlsx
```

## 🛠️ Geliştirme

### Test Modu

Excel handler'ı test etmek için:

```bash
python excel_handler.py
```

### Debug Modu

Daha detaylı log'lar için `bot.py` içinde:

```python
logging.basicConfig(level=logging.DEBUG)
```

## 📝 Notlar

- Oluşturulan teklifler `outputs/` klasöründe saklanır
- Vergi levhası PDF'leri geçici olarak işlenir ve silinir
- Teklif numaraları otomatik olarak YYMM### formatında oluşturulur

## 🐛 Sorun Giderme

### "ModuleNotFoundError" hatası
```bash
pip install -r requirements.txt
```

### Tesseract bulunamadı hatası
Tesseract'ın yüklü ve PATH'de olduğundan emin olun:
```bash
which tesseract
```

### PDF okunamıyor
- PDF'in metin tabanlı olduğundan emin olun
- Görüntü tabanlı PDF'ler için OCR gereklidir

### Bot token hatası
`.env` dosyasındaki token'ı kontrol edin ve bot.py'yi yeniden başlatın

## 📞 Destek

Sorularınız için:
- GitHub Issues açın
- Email: hatice@arslanlidanismanlik.com

## 📄 Lisans

Bu proje özel kullanım içindir.

---

**Geliştirici:** GitHub Copilot ile geliştirildi
**Tarih:** 28 Ekim 2025
