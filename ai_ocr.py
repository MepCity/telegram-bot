"""
AI-powered OCR modülü
GPT-4 Vision veya Google Vision API ile vergi levhası okuma
"""
import os
import base64
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# OpenAI API anahtarı
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# Google Cloud credentials
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')


class AIVisionOCR:
    """Yapay zeka destekli OCR"""
    
    def __init__(self, provider='openai'):
        """
        Args:
            provider: 'openai' veya 'google'
        """
        self.provider = provider
        
    def extract_tax_info(self, image_path):
        """
        AI ile vergi levhası bilgilerini çıkar
        
        Args:
            image_path: Görüntü dosya yolu
            
        Returns:
            dict: Çıkarılan bilgiler
        """
        if self.provider == 'openai':
            return self._extract_with_openai(image_path)
        elif self.provider == 'google':
            return self._extract_with_google(image_path)
        else:
            raise ValueError(f'Bilinmeyen provider: {self.provider}')
    
    def _extract_with_openai(self, image_path):
        """GPT-4 Vision ile çıkarım"""
        try:
            import openai
            
            if not OPENAI_API_KEY:
                logger.error('OPENAI_API_KEY tanımlı değil')
                return self._empty_result()
            
            openai.api_key = OPENAI_API_KEY
            
            # Görüntüyü base64'e çevir
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # GPT-4 Vision API çağrısı
            response = openai.ChatCompletion.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "Sen Türkiye vergi levhalarından bilgi çıkaran bir uzmansın. Sadece JSON formatında yanıt ver."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Bu Türkiye vergi levhası fotoğrafından aşağıdaki bilgileri çıkar ve sadece JSON formatında döndür:

{
  "company_name": "Firma ticaret ünvanı (tam olarak, LİMİTED ŞİRKETİ, ANONİM ŞİRKETİ dahil)",
  "tax_office": "Vergi dairesi adı",
  "tax_number": "10 haneli vergi kimlik numarası",
  "address": "İş yeri adresi (mahalle, cadde, şehir)"
}

Sadece JSON döndür, başka açıklama yapma."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=600,
                temperature=0.1  # Daha deterministik sonuç
            )
            
            # JSON parse et
            content = response.choices[0].message.content
            
            # Markdown code block varsa temizle
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            
            result = json.loads(content.strip())
            
            # Raw text ekle
            result['raw_text'] = f"[GPT-4 Vision]\n{json.dumps(result, ensure_ascii=False, indent=2)}"
            
            logger.info(f'GPT-4 Vision başarılı: {result.get("company_name", "")[:50]}')
            return result
            
        except Exception as e:
            logger.error(f'GPT-4 Vision hatası: {e}')
            return self._empty_result()
    
    def _extract_with_google(self, image_path):
        """Google Cloud Vision ile çıkarım"""
        try:
            from google.cloud import vision
            import os
            
            if GOOGLE_APPLICATION_CREDENTIALS:
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GOOGLE_APPLICATION_CREDENTIALS
            
            client = vision.ImageAnnotatorClient()
            
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            response = client.document_text_detection(image=image)
            
            if response.error.message:
                raise Exception(response.error.message)
            
            # Tam metni al
            full_text = response.full_text_annotation.text
            
            # Basit parsing (gelişmiş parsing için OCR kullan)
            from pdf_reader import PDFReader
            reader = PDFReader()
            info = reader._parse_ocr_text(full_text)
            info['raw_text'] = f"[Google Vision]\n{full_text}"
            
            logger.info(f'Google Vision başarılı')
            return info
            
        except Exception as e:
            logger.error(f'Google Vision hatası: {e}')
            return self._empty_result()
    
    def _empty_result(self):
        """Boş sonuç"""
        return {
            'company_name': '',
            'tax_office': '',
            'tax_number': '',
            'address': '',
            'raw_text': 'AI OCR başarısız'
        }


# Kullanım örneği
if __name__ == '__main__':
    # Test
    ocr = AIVisionOCR(provider='openai')
    
    test_image = 'foto.jpg'
    if Path(test_image).exists():
        result = ocr.extract_tax_info(test_image)
        print('AI OCR Sonuç:')
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print('Test fotoğrafı bulunamadı')
