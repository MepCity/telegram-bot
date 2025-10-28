# 🚀 Hızlı Başlangıç

## 5 Dakikada Botu Çalıştırın!

### 1️⃣ Telegram Bot Oluşturun (2 dakika)

Telegram'ı açın ve [@BotFather](https://t.me/botfather)'a gidin:

```
/newbot
```

Bot adı: `Teklif Botu`
Kullanıcı adı: `teyze_teklif_bot` (benzersiz olmalı)

**Token'ı kopyalayın!** (örn: `123456789:ABC...`)

---

### 2️⃣ Kurulumu Yapın (2 dakika)

Terminal'i açın:

```bash
cd /Users/yasir/Desktop/bot
./setup.sh
```

Kurulum bitince `.env` dosyasını düzenleyin:

```bash
nano .env
```

Token'ı yapıştırın:
```
TELEGRAM_BOT_TOKEN=sizin_tokeniniz_buraya
```

Kaydet: `Ctrl+O`, `Enter`, `Ctrl+X`

---

### 3️⃣ Botu Başlatın (30 saniye)

```bash
./start.sh
```

Şunu görmelisiniz:
```
✅ Bot çalışıyor! Durdurmak için Ctrl+C
```

---

### 4️⃣ Test Edin! (30 saniye)

Telegram'da botunuzu bulun:
1. `/start` yazın
2. `/yeni` yazın  
3. Adım adım ilerleyin!

---

## 📝 Örnek Kullanım

```
Bot: Müşteri/Yetkili adı?
Siz: Ahmet Bey

Bot: Vergi levhası PDF'i?
Siz: [PDF dosyası gönderin]

Bot: Hizmet/ürün adı?
Siz: YATIRIM TEŞVİK BELGESİ

Bot: Miktar?
Siz: 1

Bot: Birim fiyat?
Siz: 750000

Bot: Başka ürün eklemek ister misiniz?
Siz: [Hayır]

Bot: Teklif tarihi?
Siz: /bugün

Bot: Teslim tarihi?
Siz: /yok

Bot: Ödeme şekli?
Siz: /varsayilan

Bot: ✅ Teklif hazırlandı!
[Excel dosyası gönderir]
```

---

## 🎯 Hepsi Bu Kadar!

**Sorun mu yaşıyorsunuz?**
- `KULLANIM.md` - Detaylı kılavuz
- `README.md` - Teknik dokümantasyon

**Botu durdurmak için:** Terminal'de `Ctrl+C`

**Yeniden başlatmak için:** `./start.sh`

---

İyi kullanımlar! 🎉
