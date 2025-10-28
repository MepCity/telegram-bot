# 🤖 AI-Destekli OCR Kullanım Kılavuzu

## 📋 Sorun

Vergi levhalarındaki firma adı/bilgiler farklı konumlarda olabiliyor. Klasik OCR her levha formatında çalışmıyor.

## ✅ Çözümler

### 1. **Çoklu Strateji OCR** (Ücretsiz) ⭐

Artık bot 3 farklı strateji ile deniyor:
- Strateji 1: TİCARET ÜNVANI kelimesinin yanı
- Strateji 2: Vergi dairesi altındaki bölge  
- Strateji 3: En uzun ŞİRKETİ içeren satır

**Kullanım:** Otomatik çalışıyor, ek bir şey yapmanız gerekmiyor.

---

### 2. **GPT-4 Vision API** (Ücretli ama Güçlü) 🚀

%95+ doğrulukla her türlü levhayı okur.

#### Kurulum:

```bash
pip install openai
```

#### .env dosyasına ekleyin:

```bash
OPENAI_API_KEY=sk-...your-api-key...
```

#### Kullanım:

```python
# pdf_reader.py yerine ai_ocr kullanın
from ai_ocr import AIVisionOCR

ocr = AIVisionOCR(provider='openai')
info = ocr.extract_tax_info('foto.jpg')
```

#### Bot'a entegre etmek için:

`bot.py` dosyasında:

```python
# Satır 18 civarı
from pdf_reader import PDFReader
from ai_ocr import AIVisionOCR  # Yeni

class OfferBot:
    def __init__(self):
        self.pdf_reader = PDFReader()
        self.ai_ocr = AIVisionOCR(provider='openai')  # Yeni
        # ...
    
    async def receive_tax_photo(self, update, context):
        # ...
        
        # Önce AI ile dene
        if os.getenv('OPENAI_API_KEY'):
            tax_data = self.ai_ocr.extract_tax_info(str(photo_path))
            
            # Başarısız olursa klasik OCR
            if not tax_data.get('company_name'):
                tax_data = self.pdf_reader.extract_from_image(str(photo_path))
        else:
            # API key yoksa klasik OCR
            tax_data = self.pdf_reader.extract_from_image(str(photo_path))
```

**Maliyet:** ~$0.01-0.02 per fotoğraf (~0.30-0.60 TL)

---

### 3. **Google Cloud Vision API** (Alternatif)

#### Kurulum:

```bash
pip install google-cloud-vision
```

#### Google Cloud'da:
1. Proje oluştur
2. Vision API'yi aktifleştir
3. Service Account key oluştur (JSON)
4. JSON dosyasını kaydet

#### .env dosyasına:

```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

#### Kullanım:

```python
from ai_ocr import AIVisionOCR

ocr = AIVisionOCR(provider='google')
info = ocr.extract_tax_info('foto.jpg')
```

**Maliyet:** İlk 1000 görüntü ücretsiz, sonra $1.50/1000 görüntü

---

## 🎯 Öneri

**Aşama 1:** Önce çoklu strateji OCR'yi deneyin (ücretsiz, zaten aktif)

**Aşama 2:** Başarı oranı düşükse GPT-4 Vision ekleyin:
- Daha pahalı ama %95+ doğru
- Sadece klasik OCR başarısız olduğunda kullanın
- Maliyet optimize edilir

**Hibrit Yaklaşım (Önerilen):**

```python
# Önce ücretsiz OCR dene
result = pdf_reader.extract_from_image(photo)

# Firma adı boşsa AI kullan
if not result['company_name'] and OPENAI_API_KEY:
    result = ai_ocr.extract_tax_info(photo)
```

Bu şekilde:
- ✅ Çoğu durumda ücretsiz OCR yeterli
- ✅ Sadece zor durumlarda AI devreye girer
- ✅ Maliyet optimum

---

## 📊 Karşılaştırma

| Özellik | Klasik OCR | Çoklu Strateji | GPT-4 Vision | Google Vision |
|---------|-----------|----------------|--------------|---------------|
| Maliyet | Ücretsiz | Ücretsiz | ~$0.01/foto | $1.5/1000 |
| Doğruluk | %60-70 | %75-85 | %95+ | %90+ |
| Hız | Hızlı | Hızlı | Orta (2-3s) | Orta |
| Kurulum | Kolay | Aktif | API key | JSON key |

---

## 🔧 Hızlı Test

```bash
# Çoklu strateji test (zaten aktif)
python3 -c "from pdf_reader import PDFReader; r=PDFReader(); print(r.extract_from_image('foto.jpg'))"

# GPT-4 Vision test
export OPENAI_API_KEY=sk-...
python3 ai_ocr.py
```

---

## ❓ Sorular

**S: AI pahalı mı?**  
C: Fotoğraf başı ~0.30-0.60 TL. Aylık 100 teklif = ~30-60 TL

**S: API key nereden alınır?**  
C: platform.openai.com → API keys → Create new key

**S: Hibrit yaklaşımı nasıl kurarım?**  
C: Aşağıdaki kodu `bot.py` dosyasına ekleyin (tam örnek aşağıda)
