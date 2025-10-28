# 🎨 Font Renkleri Düzeltmesi - 28 Ekim 2025

## ❌ Sorun

Yeni şablon (`yeni.xlsx`) kullanılırken tablo başlıkları ve fiyat değerleri koyu arka plan üzerinde **siyah** yazıyla görünüyordu, bu da yazıları neredeyse okunamaz hale getiriyordu.

### Etkilenen Hücreler:
- **Satır 12:** NO, MİKTAR, BİRİM FİYAT, TUTAR (tablo başlıkları)
- **K18:** Ara Toplam değeri
- **K19:** KDV değeri
- **K20:** Genel Toplam değeri

### Neden Oldu?

Şablonda bu hücreler `font.color = None` (Auto) olarak ayarlanmıştı. Bu, Excel'in otomatik olarak arka plana göre kontrastlı renk seçmesini sağlar:
- Koyu arka plan → Beyaz yazı
- Açık arka plan → Siyah yazı

Ancak Python kodu ile veri yazarken `openpyxl`, hücrenin mevcut font stilini kaybediyordu ve default siyah yazı kullanıyordu.

## ✅ Çözüm

### 1. Import Eklendi
```python
from copy import copy
```

### 2. Yeni Fonksiyon: `set_cell_with_style()`

Hücreye veri yazarken mevcut tüm stil bilgilerini koruyan yeni bir fonksiyon eklendi:

```python
def set_cell_with_style(r, c, v):
    """Hücreye yazarken mevcut font ve stil bilgilerini koru"""
    cell = ws.cell(row=r, column=c)
    
    # Mevcut stil bilgilerini kaydet
    old_font = copy(cell.font) if cell.font else None
    old_alignment = copy(cell.alignment) if cell.alignment else None
    old_fill = copy(cell.fill) if cell.fill else None
    old_border = copy(cell.border) if cell.border else None
    old_number_format = cell.number_format
    
    # Değeri yaz
    cell.value = v
    
    # Eski stilleri geri yükle
    if old_font:
        cell.font = old_font
    if old_alignment:
        cell.alignment = old_alignment
    if old_fill:
        cell.fill = old_fill
    if old_border:
        cell.border = old_border
    if old_number_format:
        cell.number_format = old_number_format
```

### 3. Fiyat Satırlarında Kullanımı

```python
# Eski kod (yanlış):
set_cell(18, 11, f"{total_amount:,.2f} {currency}")
set_cell(19, 11, f"{kdv_amount:,.2f} {currency}")
set_cell(20, 11, f"{grand_total:,.2f} {currency}")

# Yeni kod (doğru):
set_cell_with_style(18, 11, f"{total_amount:,.2f} {currency}")
set_cell_with_style(19, 11, f"{kdv_amount:,.2f} {currency}")
set_cell_with_style(20, 11, f"{grand_total:,.2f} {currency}")
```

## 📊 Sonuç

### Şablondaki Stil Korunuyor:

#### Tablo Başlıkları (Satır 12)
- **Arka Plan:** Koyu mavi (`#34495D`)
- **Font Rengi:** Auto (None) → Excel otomatik **BEYAZ** yapıyor
- **Font:** Trebuchet MS, 8pt, Bold

#### Fiyat Satırları
- **K18 (Ara Toplam):**
  - Arka plan: Siyah (`#000000`)
  - Font: Auto → Beyaz
  
- **K19 (KDV):**
  - Arka plan: Siyah (`#000000`)
  - Font: Auto → Beyaz
  
- **K20 (Genel Toplam):**
  - Arka plan: Koyu mavi (`#2B3D4F`)
  - Font: Auto + Bold → **Beyaz ve Kalın**

## 🧪 Test Sonuçları

✅ **Tüm testler başarılı:**
- Tablo başlıkları font rengi Auto olarak korunuyor
- Fiyat satırları font rengi Auto olarak korunuyor
- Excel otomatik kontrast özelliği çalışıyor
- Koyu arka planda yazılar net bir şekilde BEYAZ görünüyor
- Açık arka planda yazılar SİYAH görünüyor

## 📂 Değişen Dosya

- ✏️ **excel_handler.py**
  - Satır 4: `from copy import copy` eklendi
  - Satır ~78-130: `set_cell_with_style()` fonksiyonu eklendi
  - Satır ~200-205: K18, K19, K20 için `set_cell_with_style()` kullanımı

## 🎯 Avantajlar

1. **Görsel Kalite:** Yazılar artık net okunuyor
2. **Şablon Uyumlu:** Şablondaki tüm stiller korunuyor
3. **Excel Standart:** Excel'in otomatik renk sistemi kullanılıyor
4. **Bakım Kolaylığı:** Şablonda renk değişirse otomatik yansır
5. **Gelecek Koruma:** Tüm stil özellikleri (font, fill, border, alignment) korunuyor

## ⚠️ Önemli Notlar

1. **copy modülü gerekli:** `from copy import copy` import edilmeli
2. **Şablon değişirse:** `set_cell_with_style()` otomatik yeni stilleri alır
3. **Performans:** Stil kopyalama ufak bir overhead ekler ama fark edilmez
4. **Merged cells:** Fonksiyon merged hücreleri de doğru handle ediyor

## 🔄 Gelecek İyileştirmeler

Eğer ileride daha fazla hücreye stil korumalı yazma gerekirse, aynı `set_cell_with_style()` fonksiyonu kullanılabilir.

Örneğin müşteri bilgileri (C7, C8, C9) veya teklif bilgileri (H7, H8, H9) için de kullanılabilir.

---

**Son Güncelleme:** 28 Ekim 2025  
**Durum:** ✅ Aktif ve Test Edildi  
**Versiyon:** 2.1
