# 📘 Kullanım Kılavuzu

## İlk Kurulum (Bir Kere Yapılacak)

### 1. Telegram Bot Oluşturma

1. Telegram'ı açın
2. [@BotFather](https://t.me/botfather) kullanıcısını arayın ve konuşma başlatın
3. `/newbot` komutunu gönderin
4. Bot için bir isim girin (örn: "Teklif Oluşturucu")
5. Bot için benzersiz kullanıcı adı girin (örn: "teyze_teklif_bot")
6. Aldığınız **token**'ı kopyalayın (örn: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Sistemi Kurun

Terminal'i açın ve şu komutları çalıştırın:

```bash
cd /Users/yasir/Desktop/bot
./setup.sh
```

### 3. Bot Token'ı Ekleyin

`.env` dosyasını düzenleyin:

```bash
nano .env
```

veya VS Code ile:

```bash
code .env
```

`TELEGRAM_BOT_TOKEN=your_bot_token_here` satırını bulun ve kopyaladığınız token'ı yapıştırın:

```
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

Kaydedin ve çıkın (nano'da: Ctrl+O, Enter, Ctrl+X)

### 4. Şirket Bilgilerini Güncelleyin (Opsiyonel)

Aynı `.env` dosyasında şirket bilgilerini güncelleyin:

```
COMPANY_NAME=Şirket Adınız
COMPANY_ADDRESS=Adresiniz
COMPANY_PHONE=Telefon
COMPANY_EMAIL=email@sirket.com
```

---

## Her Kullanımda

### Botu Başlatma

Terminal'de:

```bash
cd /Users/yasir/Desktop/bot
./start.sh
```

veya manuel olarak:

```bash
cd /Users/yasir/Desktop/bot
source venv/bin/activate
python bot.py
```

Konsol çıktısı şöyle olmalı:

```
🤖 Bot başlatılıyor...
📱 Bot adı: @sizin_bot_adiniz
✅ Bot çalışıyor! Durdurmak için Ctrl+C
```

### Telegram'dan Kullanım

#### Adım 1: Botu Başlatın

Telegram'da botunuzu bulun ve `/start` yazın.

Bot size karşılama mesajı gönderecek.

#### Adım 2: Yeni Teklif Oluşturun

`/yeni` yazın.

#### Adım 3: Bilgileri Girin

Bot sırayla şunları soracak:

**1. Müşteri/Yetkili Adı**
```
Ahmet Yılmaz
```

**2. Vergi Levhası PDF**
- Telefon/bilgisayardan PDF dosyasını seçin ve gönderin
- Bot otomatik olarak firma bilgilerini okuyacak

**3. Ürün/Hizmet Bilgileri**

Hizmet adı:
```
YATIRIM TEŞVİK BELGESİ
```

Miktar:
```
1
```

Birim fiyat:
```
750000
```

**4. Başka Ürün Eklemek İster misiniz?**
- `Evet` veya `Hayır` butonuna tıklayın
- Evet derseniz 3. adım tekrarlanır

**5. Teklif Tarihi**
```
28.10.2025
```
veya bugünün tarihi için:
```
/bugün
```

**6. Teslim Tarihi**
```
15.11.2025
```
veya belirtilmeyecekse:
```
/yok
```

**7. Ödeme Şekli**
```
PEŞİN
```
veya varsayılan için:
```
/varsayilan
```

#### Adım 4: Teklifi Alın

Bot teklif Excel dosyasını oluşturup size gönderecek.

Dosyayı indirebilir, düzenleyebilir veya direkt paylaşabilirsiniz.

---

## Komutlar

| Komut | Açıklama |
|-------|----------|
| `/start` | Botu başlat, yardım mesajını gör |
| `/yeni` | Yeni teklif oluşturmaya başla |
| `/iptal` | Mevcut işlemi iptal et |
| `/bugün` | Teklif tarihi sorusunda bugünün tarihini kullan |
| `/yok` | Teslim tarihi belirtilmeyecek |
| `/varsayilan` | Varsayılan ödeme şeklini kullan (PEŞİN) |

---

## İpuçları

### ✅ Vergi Levhası PDF'i

- **En iyi sonuç:** Metin tabanlı PDF (e-imza ile alınmış)
- **OCR gerekli:** Taranmış/fotoğraf PDF
- **Önemli:** PDF'de şu bilgiler olmalı:
  - Firma ünvanı
  - Vergi dairesi
  - Vergi numarası

### ✅ Fiyat Girişi

Şu formatlar kabul edilir:
- `750000` (nokta/virgülsüz)
- `750.000` (noktalı)
- `750000.50` (kuruşlu)

### ✅ Birden Fazla Ürün

Her ürün için:
1. İsim, miktar, fiyat girin
2. "Evet" seçin
3. Yeni ürün bilgilerini girin
4. Bitince "Hayır" seçin

### ✅ Teklif Düzenleme

Oluşturulan Excel dosyasını:
- Bilgisayarda Excel/LibreOffice ile düzenleyebilirsiniz
- Telefonda Google Sheets ile açabilirsiniz
- PDF'e dönüştürebilirsiniz

---

## Sorun Giderme

### Bot çalışmıyor

**Hata:** `TELEGRAM_BOT_TOKEN tanımlanmamış`

**Çözüm:** `.env` dosyasına token ekleyin

---

**Hata:** `ModuleNotFoundError`

**Çözüm:** 
```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

**Hata:** Bot mesajlara yanıt vermiyor

**Çözüm:**
1. Bot'un çalıştığından emin olun (terminal'de log görünüyor olmalı)
2. Telegram'da doğru botu kullandığınızı kontrol edin
3. `/start` yazıp yeniden deneyin

---

### PDF okumuyor

**Sorun:** Vergi levhası bilgileri çıkarılamıyor

**Çözüm:**
1. PDF'in metin tabanlı olduğundan emin olun
2. Tesseract kurulu mu kontrol edin: `tesseract --version`
3. Gerekirse Tesseract'ı yükleyin: `brew install tesseract`

---

### Excel hatası

**Sorun:** `YTB Teklif.xlsx bulunamadı`

**Çözüm:** Template dosyasının bot klasöründe olduğundan emin olun

---

## Gelişmiş Kullanım

### Botu Arka Planda Çalıştırma

```bash
cd /Users/yasir/Desktop/bot
source venv/bin/activate
nohup python bot.py > bot.log 2>&1 &
```

Durdurmak için:
```bash
ps aux | grep bot.py
kill [process_id]
```

### Logları İzleme

```bash
tail -f bot.log
```

### Otomatik Başlatma (macOS)

launchd ile sistem başlangıcında otomatik başlatma kurulumu yapılabilir.

---

## Sıkça Sorulan Sorular

**S: Birden fazla kişi aynı botu kullanabilir mi?**

C: Evet! Bot aynı anda birden fazla kullanıcıya hizmet verebilir.

---

**S: Oluşturulan teklifler nerede saklanıyor?**

C: `outputs/` klasöründe Excel formatında saklanıyor.

---

**S: PDF olarak gönderebilir mi?**

C: Şu anda Excel olarak gönderiyor. Excel'i PDF'e dönüştürmek isterseniz:
- macOS: Excel ile aç > Dosya > Farklı Kaydet > PDF
- Online: [Excel to PDF converter](https://www.ilovepdf.com/excel_to_pdf)

---

**S: Teklif şablonunu değiştirebilir miyim?**

C: Evet! `YTB Teklif.xlsx` dosyasını düzenleyin. Ancak hücre konumlarını değiştirirseniz `excel_handler.py` dosyasını da güncellemeniz gerekir.

---

## Destek

Sorun yaşarsanız:

1. `bot.log` dosyasını kontrol edin
2. Terminal çıktısını inceleyin
3. README.md'yi okuyun
4. GitHub'da issue açın

---

**Hazırlayan:** GitHub Copilot
**Tarih:** 28 Ekim 2025
**Versiyon:** 1.0
