# 🎯 Güncellenmiş Kullanım Kılavuzu

## ✨ Yeni Özellikler

✅ **Vergi levhasından otomatik firma adı çıkarma**  
✅ **%25 KDV otomatik hesaplama**  
✅ **Basitleştirilmiş akış (tarih soruları kaldırıldı)**  
✅ **Bugünün tarihi otomatik eklenir**

---

## 🚀 Hızlı Kullanım

### Telegram'da Bot Akışı

```
1. /yeni → Yeni teklif başlat

2. Vergi levhası PDF'i gönder
   ↓
   Bot otomatik okur: "SEGE TAŞIT KOLTUKLARI VE OTOMOTİV..."

3. Yetkili adı yaz
   → Örnek: "YÜKSEL BEY"

4. Hizmet adı yaz
   → Örnek: "YATIRIM TEŞVİK BELGESİ"

5. Adet yaz
   → Örnek: "1"

6. Fiyat yaz
   → Örnek: "750000"

7. Başka ürün? → "Hayır"

8. ✅ Teklif Excel'i geliyor!
   📊 Ara Toplam: 750,000.00 TL
   💰 KDV (%25): 187,500.00 TL
   🎯 Genel Toplam: 937,500.00 TL
```

---

## 📋 Örnek Senaryo

**Kullanıcı:** /yeni  
**Bot:** 📄 Vergi levhası PDF'i gönderin.

**Kullanıcı:** [VERGİ LEVHASI.pdf gönderir]  
**Bot:** ⏳ Vergi levhası okunuyor...  
**Bot:** ✅ Firma: SEGE TAŞIT KOLTUKLARI VE OTOMOTİV SANAYİ VE TİCARET ANONİM ŞİRKETİ

**Bot:** 👤 Firma yetkilisinin adını yazın:  
**Kullanıcı:** YÜKSEL BEY

**Bot:** 📦 Hizmet/ürün adını yazın:  
**Kullanıcı:** YATIRIM TEŞVİK BELGESİ

**Bot:** 🔢 Adet/Miktar:  
**Kullanıcı:** 1

**Bot:** 💰 Birim Fiyat (TL):  
**Kullanıcı:** 750000

**Bot:**  
✅ Eklendi:  
1. YATIRIM TEŞVİK BELGESİ  
• Miktar: 1  
• Fiyat: 750,000.00 TL  
*Ara Toplam:* 750,000.00 TL

**Bot:** ➕ Başka ürün eklemek ister misiniz?  
[Evet] [Hayır]

**Kullanıcı:** Hayır

**Bot:** ⏳ Teklif hazırlanıyor... (KDV ekleniyor)

**Bot:** [teklif_SEGE_TAŞIT_20251028_020936.xlsx gönderir]  
✅ Teklif başarıyla oluşturuldu!  
📊 Özet:  
• Ara Toplam: 750,000.00 TL  
• KDV (%25): 187,500.00 TL  
• Genel Toplam: 937,500.00 TL

---

## 🔧 Teknik Detaylar

### Otomatik Doldurulular
- ✅ **Müşteri Adı:** Vergi levhasından çıkarılır
- ✅ **Teklif Tarihi:** Bugünün tarihi (GG.AA.YYYY)
- ✅ **Ödeme Şekli:** PEŞİN (varsayılan)
- ✅ **Teslim Tarihi:** "--------------------"
- ✅ **KDV Oranı:** %25 (config.py'den değiştirilebilir)
- ✅ **Teklif No:** Otomatik artan (YYMM### formatı)

### Excel'de Doldurulanan Alanlar
| Satır | Alan | Kaynak |
|-------|------|--------|
| E15 | Müşteri Adı | Vergi levhası PDF |
| E16 | Firma Yetkilisi | Kullanıcı girişi |
| P15 | Teklif No | Otomatik |
| P16 | Teklif Tarihi | Bugün |
| P17 | Ödeme Şekli | PEŞİN |
| B22+ | Hizmet Adları | Kullanıcı girişi |
| O22+ | Miktarlar | Kullanıcı girişi |
| P22+ | Birim Fiyatlar | Kullanıcı girişi |
| Q22+ | Tutarlar | Otomatik (miktar × fiyat) |
| P31 | Ara Toplam | Otomatik |
| P32 | KDV (%25) | Otomatik |
| P33 | Genel Toplam | Otomatik |

---

## ⚙️ Özelleştirme

### KDV Oranını Değiştirme

`.env` dosyasında:
```bash
KDV_RATE=0.20  # %20 KDV için
KDV_RATE=0.18  # %18 KDV için
KDV_RATE=0.25  # %25 KDV için (varsayılan)
```

veya `config.py` dosyasında:
```python
KDV_RATE = float(os.getenv('KDV_RATE', '0.25'))
```

---

## 🐛 Sorun Giderme

### Vergi levhası okunamıyor

**Sorun:** Bot firma adını çıkaramıyor

**Çözüm:**
1. PDF'in doğru formatta olduğundan emin olun
2. Metin tabanlı PDF olmalı (taranmış görüntü değil)
3. "TİCARET ÜNVANI" alanı açıkça görünmeli

**Alternatif:** Manuel giriş özelliği eklenebilir (gelecek güncellemede)

---

### KDV hesabı yanlış

**Sorun:** %25 dışında KDV gerekiyor

**Çözüm:** `.env` dosyasında `KDV_RATE` değerini değiştirin

---

### Excel merge edilmiş hücreler

**Sorun:** Bazı hücreler merge edilmiş

**Çözüm:** Kod otomatik olarak doğru hücreleri buluyor (P31, P32, P33)

---

## 💡 İpuçları

✅ **Birden fazla ürün** için "Evet" seçeneğini kullanın  
✅ **Fiyat girişi** için nokta/virgül kullanmayın (750000)  
✅ **Vergi levhası** e-imza ile alınmış olmalı (daha iyi okur)  
✅ **Excel çıktısı** dilediğiniz gibi düzenlenebilir  
✅ **PDF'e çevirmek** için Excel > Farklı Kaydet > PDF

---

## 📊 Test Sonuçları

✅ **PDF Okuma:** Başarılı  
✅ **Firma Adı Çıkarma:** Başarılı  
✅ **Excel Oluşturma:** Başarılı  
✅ **KDV Hesaplama:** Başarılı (%25)  
✅ **Toplam Hesaplama:** Başarılı  

**Test Verileri:**
- Firma: SEGE TAŞIT KOLTUKLARI VE OTOMOTİV SANAYİ VE TİCARET ANONİM ŞİRKETİ
- Hizmet: YATIRIM TEŞVİK BELGESİ
- Fiyat: 750,000 TL
- KDV: 187,500 TL
- Toplam: 937,500 TL

---

**Son Güncelleme:** 28 Ekim 2025  
**Versiyon:** 2.0 (Yeni Akış)
