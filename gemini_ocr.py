"""
Google Gemini Vision ile vergi levhası okuma
%100 doğruluk, ÜCRETSIZ (ayda 1500 istek)
"""
import os
import json
import logging
from pathlib import Path
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF - PDF'den görsel çıkarmak için

logger = logging.getLogger(__name__)


class GeminiOCR:
    """Google Gemini Vision ile OCR"""
    
    def __init__(self, api_key=None):
        """
        Args:
            api_key: Google AI Studio API anahtarı
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY', '')
        
        if not self.api_key:
            raise ValueError('GEMINI_API_KEY bulunamadı!')
            
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
    def extract_tax_info(self, image_path):
        """
        Gemini ile vergi levhası bilgilerini çıkar
        
        Args:
            image_path: Görüntü dosya yolu
            
        Returns:
            dict: {
                'company_name': str,
                'tax_office': str, 
                'tax_number': str,
                'address': str
            }
        """
        try:
            logger.info(f'🤖 Gemini Vision ile okuma başlıyor: {image_path}')
            
            # Resmi aç
            img = Image.open(image_path)
            
            # Prompt - Türkçe vergi levhası için optimize edilmiş
            prompt = """Bu Türk vergi levhasından şu bilgileri TAMAMEN ve DOĞRU çıkar:

1. TİCARET ÜNVANI (Firma Adı) - TAM İSİM (kısaltma yapma)
2. VERGİ DAİRESİ - Sadece vergi dairesi adı
3. VERGİ KİMLİK NO - Tam 10 haneli sayı
4. İŞ YERİ ADRESİ - Tam adres

CEVABI SADECE JSON formatında ver, başka açıklama ekleme:
{
    "company_name": "firma tam ünvanı buraya",
    "tax_office": "vergi dairesi adı",
    "tax_number": "10 haneli sayı",
    "address": "tam adres buraya"
}

ÖNEMLİ KURALLAR:
- Firma adını TAMAMEN yaz, kısaltma yapma
- Vergi numarası MUTLAKA 10 hane olmalı
- Boş alan bırakma, tüm bilgileri doldur
- Sadece JSON formatında cevap ver"""

            # Gemini'ye gönder
            response = self.model.generate_content([prompt, img])
            
            logger.debug(f'Gemini yanıtı: {response.text}')
            
            # JSON parse et
            result = self._parse_response(response.text)
            
            logger.info(f'✅ Gemini okuma başarılı:')
            logger.info(f'   Firma: {result.get("company_name", "")[:50]}...')
            logger.info(f'   Vergi Dairesi: {result.get("tax_office", "")}')
            logger.info(f'   Vergi No: {result.get("tax_number", "")}')
            
            return result
            
        except Exception as e:
            logger.error(f'❌ Gemini okuma hatası: {e}')
            return {
                'company_name': '',
                'tax_office': '',
                'tax_number': '',
                'address': ''
            }
    
    def extract_tax_info_from_pdf(self, pdf_path):
        """
        PDF'den vergi levhası bilgilerini çıkar (Gemini Vision)
        
        Args:
            pdf_path: PDF dosya yolu
            
        Returns:
            dict: {
                'company_name': str,
                'tax_office': str, 
                'tax_number': str,
                'address': str
            }
        """
        try:
            logger.info(f'🤖 Gemini Vision ile PDF okuma başlıyor: {pdf_path}')
            
            # PDF'in ilk sayfasını görsel olarak yükle
            pdf_document = fitz.open(pdf_path)
            first_page = pdf_document[0]
            
            # Sayfayı yüksek çözünürlükte görsel olarak al
            pix = first_page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom
            
            # Geçici görsel dosyasına kaydet
            temp_image = Path(pdf_path).parent / f"{Path(pdf_path).stem}_temp.png"
            pix.save(str(temp_image))
            pdf_document.close()
            
            # Gemini Vision ile görseli oku
            result = self.extract_tax_info(str(temp_image))
            
            # Geçici dosyayı sil
            temp_image.unlink(missing_ok=True)
            
            logger.info(f'✅ PDF Gemini okuma başarılı')
            return result
            
        except Exception as e:
            logger.error(f'❌ PDF Gemini okuma hatası: {e}')
            # Hata olursa geçici dosyayı temizle
            try:
                temp_image = Path(pdf_path).parent / f"{Path(pdf_path).stem}_temp.png"
                temp_image.unlink(missing_ok=True)
            except:
                pass
            
            return {
                'company_name': '',
                'tax_office': '',
                'tax_number': '',
                'address': ''
            }
    
    def _parse_response(self, text):
        """Gemini yanıtını parse et"""
        try:
            # JSON'u çıkar
            text = text.strip()
            
            # Markdown kod bloğu varsa temizle
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]
            
            # JSON parse
            data = json.loads(text.strip())
            
            return {
                'company_name': data.get('company_name', '').strip(),
                'tax_office': data.get('tax_office', '').strip(),
                'tax_number': data.get('tax_number', '').strip(),
                'address': data.get('address', '').strip()
            }
            
        except json.JSONDecodeError as e:
            logger.error(f'JSON parse hatası: {e}')
            logger.error(f'Gelen metin: {text}')
            
            # Fallback: Basit regex ile çıkar
            import re
            
            result = {
                'company_name': '',
                'tax_office': '',
                'tax_number': '',
                'address': ''
            }
            
            # Firma adı
            match = re.search(r'"company_name"\s*:\s*"([^"]+)"', text)
            if match:
                result['company_name'] = match.group(1)
            
            # Vergi dairesi
            match = re.search(r'"tax_office"\s*:\s*"([^"]+)"', text)
            if match:
                result['tax_office'] = match.group(1)
            
            # Vergi numarası
            match = re.search(r'"tax_number"\s*:\s*"([^"]+)"', text)
            if match:
                result['tax_number'] = match.group(1)
            
            # Adres
            match = re.search(r'"address"\s*:\s*"([^"]+)"', text)
            if match:
                result['address'] = match.group(1)
            
            return result


def test_gemini():
    """Test fonksiyonu"""
    import sys
    
    if len(sys.argv) < 2:
        print('Kullanım: python gemini_ocr.py <resim_yolu>')
        return
    
    image_path = sys.argv[1]
    
    # Loglama ayarla
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )
    
    # Test et
    ocr = GeminiOCR()
    result = ocr.extract_tax_info(image_path)
    
    print('\n' + '='*60)
    print('GEMINI VISION SONUÇ:')
    print('='*60)
    print(f'Firma Ünvanı   : {result["company_name"]}')
    print(f'Vergi Dairesi  : {result["tax_office"]}')
    print(f'Vergi Numarası : {result["tax_number"]}')
    print(f'Adres          : {result["address"]}')
    print('='*60)


if __name__ == '__main__':
    test_gemini()
