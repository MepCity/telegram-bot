# 🎨 YENİ ŞABLON GÜNCELLEMESİ - 28 Ekim 2025

## ✅ YAPILAN DEĞİŞİKLİKLER

### 1. Şablon Dosyası Değiştirildi
- **Eski:** `YTB Teklif Yeni.xlsx`
- **Yeni:** `yeni.xlsx`
- **Dosya:** `config.py` → `TEMPLATE_PATH = 'yeni.xlsx'`

### 2. Hücre Konumları Güncellendi

#### Tarih ve Teklif No
- **K2:** Tarih bilgisi (Sağ üst köşe)
- **K3:** Teklif numarası (Sağ üst köşe)

#### Müşteri Bilgileri (Sol taraf)
- **C7:** Firma adı (E7:G7 merged area)
- **C8:** Firma yetkilisi (E8:G8 merged area)
- **C9:** Telefon (E9:G9 merged area)

#### Teklif Bilgileri (Sağ taraf)
- **H7:** Teklif sipariş no (H7:K7 merged area)
- **H8:** Teklif tarihi (H8:K8 merged area)
- **H9:** Ödeme şekli (H9:K9 merged area) - Sabit: "PEŞİN"
- **H10:** Teslim tarihi (H10:K10 merged area) - Boş bırakılıyor

#### Ürün Tablosu (Satır 14-16)
- **A:** Sıra numarası (NO)
- **C:** Hizmet/Ürün adı (C-D merged)
- **H:** Miktar
- **I:** Birim fiyat
- **J:** Tutar (J-K merged)

#### Fiyat Hesaplamaları
- **K18:** Ara Toplam
- **K19:** KDV (%25)
- **K20:** Genel Toplam (K20-K21 merged, mavi arka plan)

#### İmza
- **A24:** "Adı Soyadı: Hatice Arslan"
- **A25:** "İmza" (şablonda hazır)

### 3. Maksimum Ürün Sayısı
- **Eski:** 10 ürün
- **Yeni:** 3 ürün (Satır 14, 15, 16)

### 4. Print Area Ayarı
- **Eski:** Dinamik (kullanılan tüm aralık)
- **Yeni:** Sabit "A1:K26"
- A4 dikey (portrait) formatta tek sayfaya sığdırılıyor

### 5. Font ve Stil Değişiklikleri
- Şablondaki mevcut font renkleri ve stil korunuyor
- Yeni eklenen veriler için özel font ayarı yapılmıyor (şablonun default'u kullanılıyor)

## 📊 ŞABLON YAPISI

```
Satır 1:  [Logo/Başlık]
Satır 2:  [Şirket bilgileri (D2:I3)]           Tarih: DD.MM.YYYY (K2)
Satır 3:  [...]                                Teklif No: T-YYYY-XXXXX (K3)
Satır 4:  [Boş]
Satır 5:  MÜŞTERİ TEKLİF VE SİPARİŞ FORMU
Satır 6:  [Boş]
Satır 7:  Firma Adı: [...]                     Teklif Sipariş No: [...]
Satır 8:  Firma Yetkilisi: [...]               Teklif Tarihi: [...]
Satır 9:  Telefon: [...]                       Ödeme Şekli: PEŞİN
Satır 10: [Boş]                                Teslim Tarihi: [...]
Satır 11: [Boş]
Satır 12: [Tablo başlıkları hazırlık]
Satır 13: [NO] [HİZMET] [MİKTAR] [BİRİM FİYAT] [TUTAR]
Satır 14: 1    [Ürün 1]  [Miktar] [Fiyat]      [Tutar]
Satır 15: 2    [Ürün 2]  [Miktar] [Fiyat]      [Tutar]
Satır 16: 3    [Ürün 3]  [Miktar] [Fiyat]      [Tutar]
Satır 17: [Boş]
Satır 18: Ara Toplam: [...]
Satır 19: KDV (%25): [...]
Satır 20: Genel Toplam: [...]
Satır 21: [...]
Satır 22: [Boş]
Satır 23: [Notlar]
Satır 24: Adı Soyadı: Hatice Arslan
Satır 25: İmza
Satır 26: [Boş]
```

## 🧪 TEST SONUÇLARI

### Test 1: İki ürünlü teklif
- ✅ Firma bilgileri doğru yerleştirildi
- ✅ Tarih ve teklif no sağ üstte (K2, K3)
- ✅ Ürünler satır 14-15'e yerleşti
- ✅ Fiyat hesaplamaları doğru (K18, K19, K20)
- ✅ İmza bilgisi korundu
- ✅ Excel başarıyla oluşturuldu

### Test 2: Tek ürünlü teklif
- ✅ Tüm hücreler doğru dolduruldu
- ✅ Otomatik teklif numarası arttı (10001 → 10002)
- ✅ Para birimi formatı doğru (₺)

## 📝 KULLANIM

Bot kullanımı **değişmedi**. Kullanıcı deneyimi aynı:

```
1. /yeni komutu
2. Vergi levhası PDF/fotoğraf gönder
3. Yetkili kişi adı
4. Tarih seçimi (otomatik/manuel)
5. E-posta
6. Ürün/Hizmet bilgileri
7. Excel teklif alınır
```

## 🎯 AVANTAJLAR

1. **Daha Modern Tasarım:** yeni.xlsx daha güncel ve profesyonel
2. **Optimize Edilmiş:** 3 ürün için optimize (çoğu teklif 1-3 ürün içerir)
3. **Daha Temiz:** Gereksiz alanlar kaldırıldı
4. **Tutarlı Format:** Font renkleri ve stiller şablondan korunuyor
5. **Kolay Bakım:** Şablon dosyasını değiştirerek tüm teklifler güncellenir

## ⚠️ ÖNEMLİ NOTLAR

1. **Eski şablon kaldırılmadı:** `YTB Teklif Yeni.xlsx` hala mevcut ama kullanılmıyor
2. **Yedekleme önerilir:** `yeni.xlsx` dosyasını yedekleyin
3. **Şablon değişiklikleri:** `yeni.xlsx`'i düzenlerseniz, hücre konumlarını değiştirmeyin
4. **Maksimum 3 ürün:** Daha fazla ürün eklenmesi için kod değişikliği gerekir

## 📂 DEĞİŞEN DOSYALAR

- ✏️ `config.py` - TEMPLATE_PATH güncellendi
- ✏️ `excel_handler.py` - Hücre konumları ve yorumlar güncellendi
- 📄 `yeni.xlsx` - Yeni şablon dosyası aktif

## 🚀 SONRAKI ADIMLAR

Eğer şablonda değişiklik yaparsanız:

1. `yeni.xlsx` dosyasını düzenleyin
2. Hücre konumları değiştiyse `excel_handler.py`'yi güncelleyin
3. Test yapın: `python3 test.py`
4. Bot'u yeniden başlatın: `./start.sh`

---

**Son Güncelleme:** 28 Ekim 2025
**Versiyon:** 2.0
**Durum:** ✅ Aktif ve Test Edildi
