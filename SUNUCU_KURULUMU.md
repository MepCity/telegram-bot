# 🚀 Telegram Botu - Sunucu Kurulum Rehberi

## Seçenek 1: VPS Kurulumu (ÖNERİLEN)

### Adım 1: VPS Satın Al
**Önerilen Sağlayıcılar:**
- **Hetzner** (€4/ay) → https://www.hetzner.com/cloud
- **DigitalOcean** ($6/ay) → https://www.digitalocean.com
- **Vultr** ($5/ay) → https://www.vultr.com

**Minimum Gereksinimler:**
- 1 vCPU
- 1 GB RAM
- 25 GB SSD
- Ubuntu 22.04 LTS

### Adım 2: SSH Bağlantısı
```bash
ssh root@your-server-ip
```

### Adım 3: Sistem Güncellemesi
```bash
# Sistem paketlerini güncelle
sudo apt update && sudo apt upgrade -y

# Gerekli paketleri kur
sudo apt install python3 python3-pip python3-venv git libreoffice tesseract-ocr tesseract-ocr-tur -y

# LibreOffice headless modda çalışsın
sudo apt install libreoffice-writer libreoffice-calc -y
```

### Adım 4: Kullanıcı Oluştur
```bash
# Bot için özel kullanıcı oluştur (güvenlik için)
sudo adduser botuser
sudo usermod -aG sudo botuser

# Yeni kullanıcıya geç
su - botuser
```

### Adım 5: Bot Dosyalarını Yükle
```bash
# Ev dizinine git
cd ~

# Bot klasörünü oluştur
mkdir bot
cd bot

# Dosyaları yükle (3 yöntem)

# YÖNTEM 1: SCP ile (yerel bilgisayarınızdan)
# Yerel bilgisayarınızda çalıştırın:
# scp -r /Users/yasir/Desktop/bot/* botuser@your-server-ip:~/bot/

# YÖNTEM 2: Git ile (eğer GitHub'da varsa)
# git clone https://github.com/username/bot.git .

# YÖNTEM 3: Manuel upload (FileZilla, WinSCP vb.)
```

### Adım 6: Python Sanal Ortam
```bash
# Sanal ortam oluştur
python3 -m venv venv

# Aktifleştir
source venv/bin/activate

# Gereksinimleri yükle
pip install --upgrade pip
pip install -r requirements.txt
```

### Adım 7: Config Ayarları
```bash
# Config dosyasını düzenle
nano config.py

# Aşağıdaki satırları kontrol et:
# TELEGRAM_BOT_TOKEN = 'your_actual_token_here'
# GEMINI_API_KEY = 'your_gemini_key_here'

# Kaydet: CTRL+X, sonra Y, sonra ENTER
```

### Adım 8: Test Et
```bash
# Botu manuel çalıştır (test için)
python3 bot.py

# Telegram'dan /start gönder
# Çalışıyor mu kontrol et

# Durdurmak için: CTRL+C
```

### Adım 9: Systemd Servisi Oluştur (Otomatik Başlatma)
```bash
# Servis dosyası oluştur
sudo nano /etc/systemd/system/telegram-bot.service
```

**Dosya içeriği:**
```ini
[Unit]
Description=Telegram Offer Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/home/botuser/bot
Environment="PATH=/home/botuser/bot/venv/bin"
ExecStart=/home/botuser/bot/venv/bin/python3 /home/botuser/bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Servisi başlat:**
```bash
# Systemd'yi yeniden yükle
sudo systemctl daemon-reload

# Servisi etkinleştir (boot'ta otomatik başlasın)
sudo systemctl enable telegram-bot.service

# Servisi başlat
sudo systemctl start telegram-bot.service

# Durumu kontrol et
sudo systemctl status telegram-bot.service

# Logları izle
sudo journalctl -u telegram-bot.service -f
```

### Adım 10: Servis Komutları
```bash
# Servisi durdur
sudo systemctl stop telegram-bot.service

# Servisi yeniden başlat
sudo systemctl restart telegram-bot.service

# Logları görüntüle
sudo journalctl -u telegram-bot.service -n 50

# Servisi devre dışı bırak
sudo systemctl disable telegram-bot.service
```

---

## Seçenek 2: Railway.app (Kolay Deploy)

### Adım 1: Hazırlık
**Gerekli dosyaları oluştur:**

**`Procfile`** (yeni dosya oluştur):
```
worker: python3 bot.py
```

**`runtime.txt`** (yeni dosya oluştur):
```
python-3.11
```

**`railway.json`** (yeni dosya oluştur):
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python3 bot.py"
  }
}
```

### Adım 2: GitHub'a Yükle
```bash
cd /Users/yasir/Desktop/bot
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/username/telegram-bot.git
git push -u origin main
```

### Adım 3: Railway'e Deploy
1. https://railway.app → Sign up (GitHub ile)
2. "New Project" → "Deploy from GitHub repo"
3. Repository seç
4. Environment Variables ekle:
   - `TELEGRAM_BOT_TOKEN` = your_token
   - `GEMINI_API_KEY` = your_key
5. Deploy!

**Not:** Railway'de LibreOffice kurulumu gerekebilir, bu yüzden VPS daha kolay.

---

## Seçenek 3: Render.com (Ücretsiz)

### Adım 1: Gerekli Dosyalar
**`render.yaml`** oluştur:
```yaml
services:
  - type: worker
    name: telegram-bot
    env: python
    plan: free
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python3 bot.py"
    envVars:
      - key: TELEGRAM_BOT_TOKEN
        sync: false
      - key: GEMINI_API_KEY
        sync: false
```

### Adım 2: Deploy
1. https://render.com → Sign up
2. "New" → "Blueprint"
3. GitHub repo bağla
4. Environment Variables ekle
5. Deploy!

**Dezavantaj:** Ücretsiz planda 15 dakika inaktif sonra uyur (mesaj gelince açılır).

---

## ⚠️ ÖNEMLİ NOTLAR

### Güvenlik
```bash
# Firewall aktifleştir
sudo ufw enable
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP (isteğe bağlı)
sudo ufw allow 443/tcp # HTTPS (isteğe bağlı)

# Otomatik güvenlik güncellemeleri
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

### Yedekleme
```bash
# Otomatik yedekleme scripti
nano ~/backup.sh
```

**Script içeriği:**
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf ~/backups/bot_backup_$DATE.tar.gz ~/bot/outputs ~/bot/*.py ~/bot/yeni.xlsx
# Eski yedekleri sil (30 günden eski)
find ~/backups/ -name "bot_backup_*.tar.gz" -mtime +30 -delete
```

```bash
chmod +x ~/backup.sh

# Crontab ile otomatik yedekleme (her gün saat 02:00)
crontab -e
# Ekle: 0 2 * * * /home/botuser/backup.sh
```

### Monitoring
```bash
# Bot çalışıyor mu kontrol
ps aux | grep bot.py

# CPU/RAM kullanımı
htop

# Disk kullanımı
df -h

# Log boyutu
du -sh ~/bot/outputs/
```

---

## 💰 Maliyet Karşılaştırması

| Sağlayıcı | Aylık Ücret | RAM | CPU | Disk | Özellik |
|-----------|-------------|-----|-----|------|---------|
| **Hetzner** | €3.79 | 2GB | 1 vCPU | 20GB | En ucuz, güçlü |
| **DigitalOcean** | $6 | 1GB | 1 vCPU | 25GB | Kolay, popüler |
| **Vultr** | $5 | 1GB | 1 vCPU | 25GB | Hızlı deploy |
| **Railway** | $5 | 512MB | 0.5 vCPU | 1GB | Ücretsiz $5 kredi/ay |
| **Render** | ÜCRETSİZ | 512MB | 0.1 vCPU | 512MB | Uyuyor (inaktif) |
| **PythonAnywhere** | ÜCRETSİZ | Sınırlı | Sınırlı | 512MB | API sınırlamaları |

---

## 🎯 Öneri

**Senin durumun için:** **HETZNER VPS** (€3.79/ay)

**Neden?**
- ✅ En ucuz
- ✅ 2GB RAM (rahat çalışır)
- ✅ LibreOffice çalıştırabilir
- ✅ Tam kontrol
- ✅ Kolay kurulum
- ✅ Almanya'da sunucular (hızlı)

**Kurulum süresi:** 15-20 dakika  
**Bakım:** Ayda 1-2 saat (güncelleme vs.)

---

## 📞 Destek

### VPS'ye Bağlanamıyorum
```bash
# SSH key oluştur (daha güvenli)
ssh-keygen -t ed25519
# Public key'i VPS'ye ekle (provider panelinden)
```

### Bot Çalışmıyor
```bash
# Logları kontrol et
sudo journalctl -u telegram-bot.service -n 100

# Manuel çalıştır (hata mesajı görmek için)
cd ~/bot
source venv/bin/activate
python3 bot.py
```

### Disk Doldu
```bash
# Eski output dosyalarını temizle
cd ~/bot/outputs
ls -lh
rm teklif_*_202410*.xlsx  # Ekim ayı dosyalarını sil
```

### Bellek Yetersiz
```bash
# Swap alanı ekle (2GB)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## ✅ Kurulum Sonrası Kontrol Listesi

- [ ] Bot çalışıyor (systemctl status)
- [ ] Telegram'dan erişilebiliyor
- [ ] PDF oluşturma çalışıyor
- [ ] OCR çalışıyor
- [ ] Otomatik başlatma aktif (systemctl enable)
- [ ] Firewall yapılandırıldı
- [ ] Yedekleme ayarlandı
- [ ] Log rotation yapılandırıldı

---

**Hazırlayan:** AI Assistant  
**Tarih:** 29 Ekim 2025  
**Versiyon:** 1.0
