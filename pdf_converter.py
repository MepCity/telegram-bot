"""
Excel'den PDF'e dönüştürme modülü
"""
import subprocess
from pathlib import Path
import platform


class PDFConverter:
    """Excel dosyasını PDF'e çevir"""
    
    def __init__(self):
        self.system = platform.system()
    
    def excel_to_pdf(self, excel_path):
        """
        Excel dosyasını PDF'e çevir
        
        Args:
            excel_path (str): Excel dosya yolu
            
        Returns:
            str: PDF dosya yolu veya None
        """
        excel_path = Path(excel_path)
        pdf_path = excel_path.with_suffix('.pdf')
        
        try:
            # Yöntem 1: LibreOffice (macOS/Linux için en güvenilir)
            if self._convert_with_libreoffice(excel_path, pdf_path):
                return str(pdf_path)
            
            # Yöntem 2: macOS'ta Numbers kullan
            if self.system == 'Darwin':
                if self._convert_with_numbers(excel_path, pdf_path):
                    return str(pdf_path)
            
            # Yöntem 3: Python kütüphaneleri ile (basit)
            if self._convert_with_python(excel_path, pdf_path):
                return str(pdf_path)
                
        except Exception as e:
            print(f'PDF dönüştürme hatası: {e}')
        
        return None
    
    def _convert_with_libreoffice(self, excel_path, pdf_path):
        """LibreOffice ile dönüştür"""
        try:
            # LibreOffice yollarını kontrol et (sıralama önemli - Railway için)
            libreoffice_paths = [
                '/usr/bin/soffice',  # Railway/Linux
                '/usr/bin/libreoffice',  # Linux alternatif
                '/Applications/LibreOffice.app/Contents/MacOS/soffice',  # macOS
                '/usr/local/bin/libreoffice',
                'soffice',
                'libreoffice',
            ]
            
            libreoffice_cmd = None
            for path in libreoffice_paths:
                try:
                    if Path(path).exists():
                        libreoffice_cmd = path
                        break
                    # which komutu ile de kontrol et
                    result = subprocess.run(['which', path], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0 and result.stdout.strip():
                        libreoffice_cmd = result.stdout.strip()
                        break
                except:
                    continue
            
            if not libreoffice_cmd:
                print("❌ LibreOffice bulunamadı")
                return False
            
            print(f"✅ LibreOffice bulundu: {libreoffice_cmd}")
            
            # Excel'i PDF'e çevir
            output_dir = excel_path.parent
            result = subprocess.run([
                libreoffice_cmd,
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', str(output_dir),
                str(excel_path)
            ], capture_output=True, timeout=30, text=True)
            
            if result.returncode != 0:
                print(f"❌ LibreOffice hata: {result.stderr}")
            
            return result.returncode == 0 and pdf_path.exists()
            
        except Exception as e:
            print(f'LibreOffice dönüştürme hatası: {e}')
            return False
    
    def _convert_with_numbers(self, excel_path, pdf_path):
        """macOS Numbers ile dönüştür"""
        try:
            # AppleScript ile Numbers kullan
            script = f'''
            tell application "Numbers"
                open POSIX file "{excel_path}"
                delay 2
                tell document 1
                    export to POSIX file "{pdf_path}" as PDF
                end tell
                close document 1 without saving
                quit
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], capture_output=True, timeout=30)
            return result.returncode == 0 and pdf_path.exists()
            
        except Exception as e:
            print(f'Numbers dönüştürme hatası: {e}')
            return False
    
    def _convert_with_python(self, excel_path, pdf_path):
        """Python kütüphaneleri ile basit dönüştürme - Excel dosyasını kopyala"""
        # Basit çözüm: Şimdilik Excel'i PDF olarak yeniden adlandır
        # Gerçek dönüşüm için LibreOffice kullanılacak
        try:
            import shutil
            # Excel dosyasını PDF'e kopyala (geçici çözüm)
            # Not: Bu gerçek bir PDF değil, sadece Excel'in kopyası
            # Kullanıcı Excel'i PDF olarak görecek ama aslında Excel olacak
            # LibreOffice kurulunca düzgün dönüşüm yapılacak
            shutil.copy(excel_path, pdf_path.with_suffix('.xlsx.temp'))
            # Gerçek PDF dönüşümü için False döndür
            return False
        except:
            return False


if __name__ == '__main__':
    # Test
    converter = PDFConverter()
    import glob
    
    # Son oluşturulan Excel dosyasını bul
    files = sorted(glob.glob('outputs/teklif_*.xlsx'), key=lambda x: x, reverse=True)
    if files:
        excel_file = files[0]
        print(f'Test ediliyor: {excel_file}')
        pdf_file = converter.excel_to_pdf(excel_file)
        if pdf_file:
            print(f'✅ PDF oluşturuldu: {pdf_file}')
        else:
            print('❌ PDF oluşturulamadı')
            print('LibreOffice kurmak için: brew install --cask libreoffice')
    else:
        print('Test edilecek Excel dosyası bulunamadı')
