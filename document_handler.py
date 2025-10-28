"""
Word ve Excel form doldurma modülü
"""
import os
import subprocess
from datetime import datetime
from pathlib import Path
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from openpyxl import load_workbook
import config


class DocumentHandler:
    """Word ve Excel şablonlarını doldur"""
    
    def __init__(self):
        self.templates_dir = Path('gerek')
        self.template_dir = self.templates_dir  # Alias
        self.output_dir = Path('outputs')
        
    def fill_yetkilendirme_taahhutnamesi(self, tax_data, output_path=None):
        """
        Yetkilendirme Taahhütnamesi Word belgesini doldurur.
        
        Args:
            tax_data: PDF'den çıkarılan vergi bilgileri
            output_path: Çıktı dosyasının kaydedileceği yol (opsiyonel)
            
        Returns:
            str: Oluşturulan dosyanın yolu
        """
        try:
            # Şablon dosyasını aç - .docx formatında olmalı
            template_path = os.path.join(self.template_dir, 'Yetkilendirme Tahattütnamesi.docx')
            
            # Eğer .docx yoksa .doc'u dönüştür
            if not os.path.exists(template_path):
                doc_path = os.path.join(self.template_dir, 'Yetkilendirme Tahattütnamesi.doc')
                if os.path.exists(doc_path):
                    print("📄 .doc dosyasını .docx'e dönüştürüyorum...")
                    import subprocess
                    result = subprocess.run([
                        'soffice', '--headless', '--convert-to', 'docx',
                        '--outdir', self.template_dir, doc_path
                    ], capture_output=True, text=True)
                    if result.returncode != 0:
                        raise Exception(f"Dönüştürme hatası: {result.stderr}")
            
            doc = Document(template_path)
            
            # ... işaretlerini bul ve değiştir
            # İlk ... → Vergi numarası
            # İkinci ... → Firma unvanı
            replacements_made = 0
            
            for paragraph in doc.paragraphs:
                original_text = paragraph.text
                
                # Paragraftaki tüm ... işaretlerini kontrol et
                while '...' in paragraph.text and replacements_made < 2:
                    # İlk ... → vergi numarası
                    if replacements_made == 0 and tax_data.get('tax_number'):
                        paragraph.text = paragraph.text.replace('...', tax_data['tax_number'], 1)
                        replacements_made = 1
                        print(f"✓ Vergi numarası yerleştirildi: {tax_data['tax_number']}")
                    # İkinci ... → firma unvanı
                    elif replacements_made == 1 and tax_data.get('company_name'):
                        paragraph.text = paragraph.text.replace('...', tax_data['company_name'], 1)
                        replacements_made = 2
                        print(f"✓ Firma unvanı yerleştirildi: {tax_data['company_name']}")
                    else:
                        break  # Veri yoksa dur
            
            # Çıktı dosyasını kaydet
            if output_path is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = os.path.join(self.output_dir, f'Yetkilendirme_Taahhutnamesi_{timestamp}.docx')
            
            doc.save(output_path)
            print(f"✅ Yetkilendirme Taahhütnamesi oluşturuldu: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ Yetkilendirme Taahhütnamesi oluşturulurken hata: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def fill_kullanici_yetkilendirme_formu(self, tax_data, email, output_path=None):
        """
        Kullanıcı Yetkilendirme Formu Excel belgesini doldurur.
        
        Args:
            tax_data: PDF'den çıkarılan vergi bilgileri
            email: Firma e-posta adresi
            output_path: Çıktı dosyasının kaydedileceği yol (opsiyonel)
            
        Returns:
            str: Oluşturulan dosyanın yolu
        """
        try:
            # Şablon dosyasını aç
            template_path = os.path.join(self.template_dir, 'Kullanıcı Yetkilendirme Formu.xlsx')
            wb = load_workbook(template_path)
            ws = wb.active
            
            # Excel yapısına göre direkt hücreleri doldur
            # E6: Firma Adı/Unvanı
            ws['E6'] = tax_data.get('company_name', '')
            print(f"✓ Firma unvanı E6'ya yazıldı: {tax_data.get('company_name', '')[:50]}")
            
            # E7: Vergi No
            ws['E7'] = tax_data.get('tax_number', '')
            print(f"✓ Vergi numarası E7'ye yazıldı: {tax_data.get('tax_number', '')}")
            
            # E8: Adres
            ws['E8'] = tax_data.get('address', '')
            print(f"✓ Adres E8'e yazıldı: {tax_data.get('address', '')[:50]}")
            
            # E9: E-posta Adresi
            ws['E9'] = email
            print(f"✓ E-posta E9'a yazıldı: {email}")
            
            # E11-E19: Hatice Arslan bilgileri (şablonda zaten dolu, değiştirmiyoruz)
            
            # Çıktı dosyasını kaydet
            if output_path is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = os.path.join(self.output_dir, f'Kullanici_Yetkilendirme_Formu_{timestamp}.xlsx')
            
            wb.save(output_path)
            print(f"✅ Kullanıcı Yetkilendirme Formu oluşturuldu: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ Kullanıcı Yetkilendirme Formu oluşturulurken hata: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def convert_to_pdf(self, input_path):
        """
        Word veya Excel dosyasını PDF'e çevir (LibreOffice kullanarak)
        
        Args:
            input_path (str): Dönüştürülecek dosya
            
        Returns:
            str: PDF dosyasının yolu veya None
        """
        input_path = Path(input_path)
        output_dir = input_path.parent
        
        try:
            # LibreOffice ile PDF'e çevir
            result = subprocess.run([
                'soffice',
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', str(output_dir),
                str(input_path)
            ], capture_output=True, timeout=30)
            
            if result.returncode == 0:
                pdf_path = input_path.with_suffix('.pdf')
                if pdf_path.exists():
                    return str(pdf_path)
            
            print(f'LibreOffice conversion failed: {result.stderr}')
            return None
            
        except Exception as e:
            print(f'PDF conversion error: {e}')
            return None
    
    def fill_sozlesme(self, tax_data, proje_turu, ucret_bilgisi, output_path=None):
        """
        Sözleşme Word belgesini doldurur.
        
        Args:
            tax_data: PDF'den çıkarılan vergi bilgileri
            proje_turu: Proje türü (ör: "TÜBİTAK 1501 PROJESİ")
            ucret_bilgisi: Ücret bilgisi dict {
                'tutar': str,  # Örn: "80.000 TL'nin %5'i"
                'aciklama': str  # Örn: "projenin onaylanması ile onaylanan tutar üzerinden %5'i"
            }
            output_path: Çıktı dosyasının kaydedileceği yol (opsiyonel)
            
        Returns:
            str: Oluşturulan dosyanın yolu
        """
        try:
            # Şablon dosyasını aç - .docx formatında olmalı
            template_path = os.path.join(self.template_dir, 'Sözleşme.docx')
            
            if not os.path.exists(template_path):
                raise Exception(f"Şablon bulunamadı: {template_path}")
            
            doc = Document(template_path)
            
            # Firma adı ve vergi numarası
            company_name = tax_data.get('company_name', '')
            tax_number = tax_data.get('tax_number', '')
            
            # Metni değiştir
            for para in doc.paragraphs:
                # 1. ... (....) → Firma adı (Vergi No)
                if '... (....)' in para.text:
                    para.text = para.text.replace('... (....)', f'{company_name} ({tax_number})')
                    print(f"✓ Firma bilgisi yerleştirildi: {company_name} ({tax_number})")
                
                # 2. ... hazırlanması → Proje türü
                if '... hazırlanması' in para.text:
                    para.text = para.text.replace('... hazırlanması', f'{proje_turu.upper()} hazırlanması')
                    print(f"✓ Proje türü yerleştirildi: {proje_turu.upper()}")
                
                # 3. ... TL projenin → Ücret tutarı
                if '... TL projenin' in para.text:
                    para.text = para.text.replace('... TL projenin', f"{ucret_bilgisi['tutar']} projenin")
                    print(f"✓ Ücret tutarı yerleştirildi: {ucret_bilgisi['tutar']}")
                
                # 4. ... talep edilir → Ücret açıklaması
                if '... talep edilir' in para.text:
                    para.text = para.text.replace('... talep edilir', f"{ucret_bilgisi['aciklama']} talep edilir")
                    print(f"✓ Ücret açıklaması yerleştirildi: {ucret_bilgisi['aciklama']}")
            
            # Çıktı dosyasını kaydet
            if not output_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_company = company_name[:30].replace('/', '_').replace('\\', '_')
                filename = f'Sozlesme_{safe_company}_{timestamp}.docx'
                output_path = os.path.join(self.output_dir, filename)
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            doc.save(output_path)
            
            print(f'✅ Sözleşme oluşturuldu: {output_path}')
            return output_path
            
        except Exception as e:
            print(f'❌ Sözleşme doldurma hatası: {e}')
            import traceback
            traceback.print_exc()
            return None


if __name__ == '__main__':
    # Test
    handler = DocumentHandler()
    
    test_data = {
        'company_name': 'STİLLA OTOMOTİV TURİZM İNŞAAT TEKSTİL İTHALAT VE İHRACAT SANAYİ LİMİTED ŞİRKETİ',
        'tax_number': '1234567890',
        'address': 'VEYSEL KARANİ MAH. ESKİ GEMLİK YOLU CAD. NO: 236 F'
    }
    
    # Word
    word_path = handler.fill_yetkilendirme_taahhutnamesi(test_data)
    print(f'Word oluşturuldu: {word_path}')
    
    # Excel
    excel_path = handler.fill_kullanici_yetkilendirme_formu(test_data, 'test@example.com')
    print(f'Excel oluşturuldu: {excel_path}')
