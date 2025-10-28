"""
PDF okuma ve OCR modülü
"""
import pdfplumber
import re
from pathlib import Path
import logging

# OCR kütüphaneleri
try:
    import pytesseract
    from pytesseract import Output
    from PIL import Image, ImageEnhance
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    Output = None

# OpenCV (görüntü iyileştirme için)
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

logger = logging.getLogger(__name__)


class PDFReader:
    """PDF'den metin ve veri çıkarma"""
    
    def __init__(self):
        pass
    
    def extract_tax_info(self, pdf_path):
        """
        Vergi levhasından bilgi çıkar
        
        Args:
            pdf_path (str): PDF dosya yolu
            
        Returns:
            dict: Çıkarılan bilgiler
                - company_name: Firma ünvanı
                - tax_office: Vergi dairesi
                - tax_number: Vergi numarası
                - address: Adres
        """
        text = self._extract_text_from_pdf(pdf_path)
        
        # Bilgileri regex ile çıkar
        info = {
            'company_name': '',
            'tax_office': '',
            'tax_number': '',
            'address': '',
            'raw_text': text  # Debug için
        }
        
        # Ticaret Ünvanı - satır satır yaklaşımı
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'TİCARET ÜNVANI' in line:
                # Bu satırdaki "TİCARET ÜNVANI" sonrasını al
                company_name = line.split('TİCARET ÜNVANI')[-1].strip()
                
                # "VERGİ KİMLİK" varsa öncesini al (aynı satırda olabilir)
                if 'VERGİ KİMLİK' in company_name:
                    company_name = company_name.split('VERGİ KİMLİK')[0].strip()
                
                # Şirket türü kelimeleri listesi (büyük-küçük harf duyarsız)
                company_keywords = [
                    'limited şirketi', 'anonim şirketi', 'şirketi',
                    'limited', 'anonim', 'a.ş.', 'ltd.', 'şti.',
                    'kollektif şirketi', 'komandit şirketi'
                ]
                
                # Sonraki 2 satırı da kontrol et (şirket türü devam edebilir)
                for j in range(1, 3):
                    if i+j >= len(lines):
                        break
                    next_line = lines[i+j].strip()
                    
                    # Boş satır ise dur
                    if not next_line:
                        break
                    
                    # "TİCARET" kelimesi varsa onu çıkar (satır başında olabilir)
                    if next_line.startswith('TİCARET '):
                        next_line = next_line.replace('TİCARET ', '', 1).strip()
                    
                    # Şirket türü içeriyorsa, "VERGİ" ve "NO" öncesini al
                    # Türkçe karakterler için upper() ile karşılaştır
                    next_upper = next_line.upper()
                    company_keywords_upper = ['LİMİTED', 'ŞİRKETİ', 'ANONİM', 'A.Ş.', 'LTD', 'ŞTİ']
                    
                    if any(keyword in next_upper for keyword in company_keywords_upper):
                        # VERGİ veya NO varsa öncesini al
                        for stopper in ['VERGİ', 'NO', 'TC']:
                            if stopper in next_line:
                                next_line = next_line.split(stopper)[0].strip()
                                break
                        if next_line:  # Boş değilse ekle
                            company_name += ' ' + next_line
                    else:
                        # Şirket türü yok ama sayı/kod varsa devam etme
                        if any(char.isdigit() for char in next_line):
                            break
                
                info['company_name'] = company_name.strip()
                break
        
        # Vergi dairesi - "DAİRESİ" sütunu altındaki değer
        vd_pattern = r'VERGİ\s+DAİRESİ\s+(\S+)'
        match = re.search(vd_pattern, text, re.IGNORECASE)
        if match:
            info['tax_office'] = match.group(1).strip()
        
        # Alternatif pattern
        if not info['tax_office']:
            vd_pattern2 = r'DAİRESİ\s+([A-ZĞÜŞİÖÇ]+)'
            match = re.search(vd_pattern2, text)
            if match:
                info['tax_office'] = match.group(1).strip()
        
        # Vergi numarası çıkarma: PDF'lerde rakamlar ayrık çıkabilir.
        # Ancak TAKVİM, MATRAH gibi tablosal verilerdeki yanlış pozitifleri engelle
        tax_candidates = []

        # Önce problematik satırları tespit et
        lines = text.split('\n')
        problem_lines = []
        for i, line in enumerate(lines):
            # TAKVİM, MATRAH, BEYAN içeren satırları not al
            if any(word in line.upper() for word in ['TAKVİM', 'MATRAH', 'BEYAN', 'TAHAKKUK', 'OLUNAN']):
                problem_lines.append(i)
        
        # regex: 10 rakamı, arada boşluk/dot/ - olmasına izin ver
        digit_like = re.compile(r'((?:\d[\s\.\-]?){10,15})')
        for m in digit_like.finditer(text):
            raw = m.group(1)
            digits = re.sub(r'\D', '', raw)
            if len(digits) == 10:
                # Bu 10 haneli sayının hangi satırda olduğunu bul
                line_num = text[:m.start()].count('\n')
                
                # Problem satırlarında ise atla
                if line_num in problem_lines or (line_num-1) in problem_lines or (line_num+1) in problem_lines:
                    continue
                    
                # Yanlış pozitiflerden kaçın: çok fazla boşluk/nokta varsa atla
                if raw.count(' ') > 2 or raw.count('.') > 1:
                    continue
                    
                tax_candidates.append((m.start(), digits))

        # Eğer kandidat bulunduysa, tercih sırası: yakınında 'VERGİ' veya 'KİMLİK' geçen ilk olan
        chosen = None
        if tax_candidates:
            # Bulunduğu index'e göre en yakın ilgili anahtar kelimeye uzaklığı ölç
            markers = ['VERGİ KİMLİK', 'TC KİMLİK', 'T.C. KİMLİK', 'VERGİ NO']
            vergis = []
            for mk in markers:
                vergis += [m.start() for m in re.finditer(re.escape(mk), text, re.IGNORECASE)]
            if vergis:
                best = None
                best_dist = None
                for idx, digits in tax_candidates:
                    # en yakın vergis pozisyonunu bul
                    dist = min(abs(idx - v) for v in vergis)
                    # Çok uzaktaysa (>150 karakter) alma
                    if dist > 150:
                        continue
                    if best is None or dist < best_dist:
                        best = digits
                        best_dist = dist
                chosen = best

            if chosen:
                info['tax_number'] = chosen            # Eğer halen vergi numarası yoksa, ileri seviye PDF analizi dene
            if not info.get('tax_number'):
                advanced_tax = self._extract_tax_number_advanced(pdf_path)
                if advanced_tax:
                    info['tax_number'] = advanced_tax
            
        # Eğer halen vergi numarası yoksa, manuel giriş için boş bırak
        # (Bot'ta kullanıcıya sorulacak)
        if not info.get('tax_number'):
            info['tax_number'] = ''  # Boş string - bot'ta kontrol edilecek        # Adres çıkarma: Özel strateji - MAH/CAD içeren satırı bul, sonra şehir satırını ekle
        lines = text.split('\n')
        addr = ''
        address_keywords = ('MAH.', 'MAHALLE', 'CAD.', 'SOK.', 'SK.', 'CADDE', 'NO:', 'KAPI NO', 'SOKAK', 'BULVAR', 'MAH', 'KAPT', 'KÖY')
        
        for i, line in enumerate(lines):
            up = line.upper()
            if any(k in up for k in address_keywords):
                # Adres satırını temizle (TC KİMLİK vb. kalıntıları çıkar)
                addr_line = re.split(r'TC\s*KİMLİK|T\.C\.|VERGİ', line, flags=re.IGNORECASE)[0].strip()
                
                # Sonraki satırları kontrol et - şehir bilgisi için
                city_line = ''
                for j in range(i+1, min(i+4, len(lines))):
                    nxt = lines[j].strip()
                    # İŞ YERİ ADRESİ başlığını atla
                    if 'İŞ YERİ' in nxt.upper() or 'ADRES' in nxt.upper():
                        continue
                    # İŞE BAŞLAMA, VERGİ TÜRÜ gibi diğer alanları atla
                    if any(stopper in nxt.upper() for stopper in ['İŞE BAŞLAMA', 'VERGİ TÜRÜ', 'VERGİ DAİRE', 'FAX', 'TEL']):
                        break
                    # Şehir formatı (ör: OSMANGAZİ/ BURSA)
                    if nxt and ('/' in nxt or len(nxt.split()) <= 3):
                        city_line = nxt
                        break
                
                # Birleştir
                if city_line:
                    addr = f"{addr_line} {city_line}"
                else:
                    addr = addr_line
                
                addr = re.sub(r'\s+', ' ', addr).strip()
                break

        # Fallback: 'İŞ YERİ ADRESİ' başlığından sonraki satırları al
        if not addr:
            for i, line in enumerate(lines):
                if 'İŞ YERİ ADRESİ' in line.upper():
                    addr_parts = []
                    for j in range(1, 3):
                        if i + j < len(lines):
                            nxt = lines[i + j].strip()
                            if nxt and not any(stopper in nxt.upper() for stopper in ['İŞE BAŞLAMA', 'VERGİ TÜRÜ']):
                                addr_parts.append(nxt)
                    if addr_parts:
                        addr = ' '.join(addr_parts)
                    break

        if addr:
            info['address'] = addr
        
        return info
    
    def _extract_text_from_pdf(self, pdf_path):
        """PDF'den metin çıkar (pdfplumber ile)"""
        text = ''
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
        except Exception as e:
            print(f'pdfplumber hatası: {e}')
            # Alternatif: OCR dene
            text = self._extract_text_with_ocr(pdf_path)
        
        return text
    
    def _extract_tax_number_advanced(self, pdf_path):
        """Vergi numarasını PDF pozisyon analizi ile çıkar"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page = pdf.pages[0]
                
                # Kelime bazlı çıkarım - VERGİ KİMLİK ve NO kelimelerinin pozisyonlarını bul
                words = page.extract_words()
                
                # VERGİ KİMLİK kelimesinin y pozisyonunu bul
                vergi_y = None
                for w in words:
                    if 'VERG' in w['text'] and 'KİMLİK' in page.extract_text()[page.extract_text().find(w['text']):page.extract_text().find(w['text'])+50]:
                        vergi_y = w['top']
                        break
                
                if vergi_y:
                    # Aynı y seviyesinde (±10 piksel) olan rakamları bul
                    numbers = []
                    for w in words:
                        if abs(w['top'] - vergi_y) < 15 and w['text'].isdigit():
                            numbers.append((w['x0'], w['text']))
                    
                    # x pozisyonuna göre sırala ve birleştir
                    numbers.sort()
                    tax_num = ''.join([n[1] for n in numbers])
                    
                    if len(tax_num) >= 10:
                        return tax_num[:10]
                
                # Alternatif: Tüm karakterleri tara
                chars = page.chars
                char_groups = {}
                
                for char in chars:
                    if char['text'].isdigit():
                        y = round(char['top'], 0)
                        if y not in char_groups:
                            char_groups[y] = []
                        char_groups[y].append((char['x0'], char['text']))
                
                # Her y seviyesinde 10 haneli sayı ara
                for y, chars_list in char_groups.items():
                    chars_list.sort()
                    num = ''.join([c[1] for c in chars_list])
                    if len(num) == 10:
                        return num
                        
        except Exception as e:
            print(f'İleri seviye vergi no çıkarma hatası: {e}')
        
        return None
    
    def _extract_text_with_ocr(self, pdf_path):
        """PDF'i OCR ile oku (görüntü tabanlı PDF'ler için)"""
        text = ''
        
        try:
            # PDF'i görüntüye çevir ve OCR uygula
            # Not: Bu kısım pdf2image kütüphanesi gerektirir
            # Şimdilik basitleştirilmiş versiyon
            pass
        except Exception as e:
            print(f'OCR hatası: {e}')
        
        return text
    
    def extract_from_image(self, image_path):
        """
        Vergi levhası fotoğrafından bilgi çıkar (OCR ile)
        
        Args:
            image_path (str): Fotoğraf dosya yolu
            
        Returns:
            dict: Çıkarılan bilgiler
        """
        if not OCR_AVAILABLE:
            return {
                'company_name': '',
                'tax_office': '',
                'tax_number': '',
                'address': '',
                'raw_text': 'OCR kütüphanesi yüklü değil'
            }
        
        try:
            # Fotoğrafı aç
            image = Image.open(image_path)
            
            # Birden fazla OCR denemesi yap
            ocr_results = []
            
            # 1. Normal OCR
            try:
                text1 = pytesseract.image_to_string(image, lang='tur', config='--psm 6')
                ocr_results.append(('normal', text1))
            except:
                text1 = pytesseract.image_to_string(image, config='--psm 6')
                ocr_results.append(('normal', text1))
            
            # 2. OpenCV ile iyileştirilmiş OCR
            if CV2_AVAILABLE:
                enhanced_images = self._preprocess_image_opencv(image_path)
                for method, enhanced_img in enhanced_images:
                    try:
                        # OpenCV görüntüsünü PIL'e çevir
                        pil_img = Image.fromarray(enhanced_img)
                        text = pytesseract.image_to_string(pil_img, lang='tur', config='--psm 6')
                        ocr_results.append((method, text))
                    except Exception as e:
                        logger.debug(f'OpenCV {method} OCR hatası: {e}')
            
            # 3. PIL ile kontrast artırma
            try:
                enhancer = ImageEnhance.Contrast(image)
                enhanced = enhancer.enhance(2.0)
                enhancer = ImageEnhance.Sharpness(enhanced)
                enhanced = enhancer.enhance(2.0)
                text3 = pytesseract.image_to_string(enhanced, lang='tur', config='--psm 6')
                ocr_results.append(('contrast', text3))
            except Exception as e:
                logger.debug(f'PIL enhancement hatası: {e}')
            
            # Tüm OCR sonuçlarından bilgileri çıkar
            temp_info = {
                'company_name': '',
                'tax_office': '',
                'tax_number': '',
                'address': '',
                'raw_text': ''
            }
            
            # Her OCR sonucunu analiz et
            best_tax_number = ''
            all_texts = []
            
            for method, text in ocr_results:
                all_texts.append(f"[{method}]\n{text}\n")
                info = self._parse_ocr_text(text)
                
                # En iyi sonuçları birleştir
                if info['company_name'] and len(info['company_name']) > len(temp_info['company_name']):
                    temp_info['company_name'] = info['company_name']
                
                if info['tax_office'] and not temp_info['tax_office']:
                    temp_info['tax_office'] = info['tax_office']
                
                if info['address'] and len(info['address']) > len(temp_info['address']):
                    temp_info['address'] = info['address']
                
                # Vergi numarası - 10 haneli olanı tercih et
                if info['tax_number']:
                    if len(info['tax_number']) == 10:
                        best_tax_number = info['tax_number']
                        break  # 10 haneli bulunca dur
                    elif len(info['tax_number']) > len(best_tax_number):
                        best_tax_number = info['tax_number']
            
            temp_info['tax_number'] = best_tax_number
            
            # Firma adı halen boşsa, konum bazlı OCR dene
            if not temp_info['company_name']:
                try:
                    company_from_position = self._extract_company_name_by_position(image_path)
                    if company_from_position:
                        temp_info['company_name'] = company_from_position
                except Exception as e:
                    logger.debug(f'Konum bazlı firma adı çıkarma hatası: {e}')
            
            temp_info['raw_text'] = '\n=====\n'.join(all_texts)
            
            return temp_info
            
        except Exception as e:
            logger.error(f'OCR hatası: {e}')
            return {
                'company_name': '',
                'tax_office': '',
                'tax_number': '',
                'address': '',
                'raw_text': f'OCR hatası: {e}'
            }
    
    def _preprocess_image_opencv(self, image_path):
        """
        OpenCV ile görüntü iyileştirme - vergi numarasını daha iyi okumak için
        
        Returns:
            list: (method_name, processed_image) tuple'ları
        """
        if not CV2_AVAILABLE:
            return []
        
        try:
            # Görüntüyü oku
            img = cv2.imread(str(image_path))
            if img is None:
                return []
            
            results = []
            
            # 1. Gri tonlama + Adaptive Threshold
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 2. Gürültü azaltma
            denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
            
            # 3. Adaptive threshold (metin belirginleştirme)
            adaptive = cv2.adaptiveThreshold(
                denoised, 255, 
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 
                11, 2
            )
            results.append(('adaptive', adaptive))
            
            # 4. Otsu threshold
            _, otsu = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            results.append(('otsu', otsu))
            
            # 5. Morphological işlemler (küçük gürültüleri temizle)
            kernel = np.ones((2, 2), np.uint8)
            morph = cv2.morphologyEx(adaptive, cv2.MORPH_CLOSE, kernel)
            results.append(('morph', morph))
            
            # 6. Görüntüyü büyüt (küçük rakamlar için)
            scaled = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            _, scaled_thresh = cv2.threshold(scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            results.append(('scaled', scaled_thresh))
            
            return results
            
        except Exception as e:
            logger.error(f'OpenCV preprocessing hatası: {e}')
            return []
    
    def _parse_ocr_text(self, text):
        """
        OCR metninden vergi levhası bilgilerini çıkar
        
        Args:
            text: OCR ile okunan metin
            
        Returns:
            dict: Çıkarılan bilgiler
        """
        info = {
            'company_name': '',
            'tax_office': '',
            'tax_number': '',
            'address': ''
        }
        
        if not text:
            return info
        
        lines = text.split('\n')
        
        # Firma ünvanını çıkar - daha esnek yaklaşım
        vergi_idx = -1
        dairesi_idx = -1
        vergi_kimlik_idx = -1
        
        for i, line in enumerate(lines):
            line_upper = line.upper()
            
            # VERGİ kelimesini bul
            if vergi_idx == -1 and 'VERGİ' in line_upper and 'LEV' not in line_upper:
                vergi_idx = i
            
            # DAİRESİ veya Vergi Dairesi sütun başlığı
            if vergi_idx != -1 and dairesi_idx == -1:
                if 'DAİRESİ' in line_upper or 'DAİRE' in line_upper:
                    dairesi_idx = i
            
            # VERGİ KİMLİK kelimesini bul
            if 'VERGİ' in line_upper and ('KİMLİK' in line_upper or 'KIMLIK' in line_upper):
                vergi_kimlik_idx = i
                break
        
        # Vergi dairesi çıkarımı - daha agresif
        # 1. "ERTUĞRULGAZİ" gibi büyük harfli kelimeyi ara
        if not info['tax_office']:
            for i, line in enumerate(lines):
                # "ADI SOYADI ERTUĞRULGAZİ" formatını yakala
                if 'ADI SOYADI' in line.upper():
                    parts = line.split()
                    # Son kelime genelde vergi dairesi
                    if len(parts) >= 2:
                        last_word = parts[-1].strip()
                        if len(last_word) >= 5 and last_word.replace('İ', '').replace('Ğ', '').replace('Ü', '').replace('Ş', '').replace('Ç', '').replace('Ö', '').isalpha():
                            info['tax_office'] = last_word
                            break
        
        # 2. Büyük harfli tek kelime ara
        if not info['tax_office']:
            for i, line in enumerate(lines):
                line_clean = line.strip()
                # Sadece büyük harfli, 5+ karakter, tek kelime
                if line_clean.isupper() and len(line_clean) >= 5 and ' ' not in line_clean:
                    # Sayı veya özel karakter yoksa
                    if not any(c.isdigit() or c in '|!$@#%^&*()' for c in line_clean):
                        # VERGİ/DAİRESİ/ÜNVANI kelimelerini içermiyorsa
                        if not any(word in line_clean for word in ['VERGİ', 'DAİRESİ', 'ÜNVANI', 'ADI', 'SOYADI', 'LEVHA']):
                            info['tax_office'] = line_clean
                            break
        
        # Firma ünvanı - TİCARET ÜNVANI satırından VERGİ KİMLİK satırına kadar
        if dairesi_idx != -1 and vergi_kimlik_idx != -1:
            company_parts = []
            for i in range(dairesi_idx + 1, min(vergi_kimlik_idx + 2, len(lines))):  # +2 çünkü devam edebilir
                line = lines[i].strip()
                if not line or len(line) < 3:
                    continue
                
                # VERGİ KİMLİK içeriyorsa öncesini al ve dur
                if 'VERGİ' in line.upper() and 'KİMLİK' in line.upper():
                    # "SEGE MOTORLU ... VERGİKİMLİK" formatı
                    parts = re.split(r'VERGİ\s*K[İI]ML[İI]K', line, flags=re.IGNORECASE)
                    before_vk = parts[0].strip()
                    
                    # Pipe ve özel karakterleri temizle
                    before_vk = re.sub(r'[|!]', '', before_vk)
                    
                    if before_vk and len(before_vk) > 5:
                        company_parts.append(before_vk)
                    break
                
                # ŞİRKETİ kelimesini içeriyorsa al ve dur
                if 'ŞİRKETİ' in line.upper():
                    # NO ve rakamları çıkar
                    line_clean = re.sub(r'NO\s+\d+', '', line, flags=re.IGNORECASE)
                    line_clean = re.sub(r'[|!]', '', line_clean).strip()
                    
                    if line_clean and len(line_clean) > 5:
                        company_parts.append(line_clean)
                    break
                
                # Özel karakterleri temizle
                line_clean = re.sub(r'[|!]', '', line)
                line_clean = line_clean.strip()
                
                # Çok kısa veya sadece özel karakterse atla
                if len(line_clean) > 5 and not all(c in '|-!İı ' for c in line_clean):
                    company_parts.append(line_clean)
            
            if company_parts:
                # Tüm parçaları birleştir
                company_text = ' '.join(company_parts)
                
                # Temizle
                company_text = re.sub(r'\s+', ' ', company_text).strip()
                
                # "GARET ÜNVANI" gibi kırık başlıkları çıkar
                if 'ÜNVAN' in company_text.upper():
                    # ÜNVANI kelimesinden sonrasını al
                    parts = re.split(r'[İI]\s*GARET\s+ÜNVAN[İI]', company_text, flags=re.IGNORECASE)
                    if len(parts) > 1:
                        company_text = parts[-1].strip()
                    else:
                        parts = re.split(r'ÜNVAN[İI]', company_text, flags=re.IGNORECASE)
                        if len(parts) > 1:
                            company_text = parts[-1].strip()
                
                # Pipe ve tırnak karakterlerini temizle
                company_text = company_text.replace('|', '').replace('"', '').strip()
                
                # Gereksiz boşlukları temizle
                company_text = re.sub(r'\s+', ' ', company_text)
                
                if len(company_text) > 5:
                    info['company_name'] = company_text
        
        # Alternatif: TİCARET ÜNVANI pattern'i
        if not info['company_name']:
            pattern = r'ÜNVAN[İI][^\n]*?([A-ZĞÜŞİÖÇ][A-ZĞÜŞİÖÇa-zğüşıöç\s]{10,}(?:LİMİTED|ŞİRKETİ|A\.Ş\.|LTD))'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info['company_name'] = match.group(1).strip()
        
        # Vergi numarası - daha agresif arama
        found_vn = None
        
        # Strateji 1: NO kelimesinden sonraki rakamlar (boşluklarla bile)
        vn_patterns = [
            r'NO[:\s]+(\d[\s\-\.]*\d[\s\-\.]*\d[\s\-\.]*\d[\s\-\.]*\d[\s\-\.]*\d[\s\-\.]*\d[\s\-\.]*\d[\s\-\.]*\d[\s\-\.]*\d)',  # 10 hane boşluklu
            r'NO[:\s]+(\d{10})',  # 10 hane
            r'KİMLİK[^\d]*(\d[\s\-\.]*\d[\s\-\.]*\d[\s\-\.]*\d[\s\-\.]*\d[\s\-\.]*\d[\s\-\.]*\d[\s\-\.]*\d[\s\-\.]*\d[\s\-\.]*\d)',  # KİMLİK sonrası 10 hane
            r'(\d{10})',  # Herhangi bir 10 haneli sayı
            r'NO[:\s]+(\d{9,11})',  # 9-11 hane
        ]
        
        for pattern in vn_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                raw_num = match.group(1)
                # Sadece rakamları al
                clean_num = re.sub(r'\D', '', raw_num)
                if 9 <= len(clean_num) <= 11:
                    found_vn = clean_num[:10] if len(clean_num) >= 10 else clean_num
                    if len(found_vn) == 10:
                        break  # 10 haneli bulunca dur
        
        if found_vn:
            info['tax_number'] = found_vn
        
        # Adres
        address_keywords = ('MAH.', 'MAH', 'CAD.', 'CAD', 'SOK.', 'SK.', 'SOKAK', 'BULVAR', 'NO:', 'İŞ YERİ ADRESİ')
        addr_found_idx = -1
        
        for i, line in enumerate(lines):
            line_upper = line.upper()
            if any(kw in line_upper for kw in address_keywords):
                addr_found_idx = i
                break
        
        if addr_found_idx != -1:
            addr_parts = []
            for j in range(addr_found_idx, min(addr_found_idx + 3, len(lines))):
                nxt = lines[j].strip()
                if not nxt:
                    continue
                if any(stop in nxt.upper() for stop in ['İŞE BAŞLAMA', 'VERGİ TÜRÜ', 'KURUMLAR VERGİSİ', 'ANA FAALİYET', 'TAKVİM']):
                    break
                
                # Temizle
                nxt = re.split(r'TC\s+K[İI]ML[İI]K', nxt, flags=re.IGNORECASE)[0].strip()
                nxt = re.sub(r'[|!]', '', nxt).strip()
                
                # İŞ YERİ ADRESİ başlığını çıkar
                nxt = re.sub(r'İŞ\s+YERİ\s+ADRESİ', '', nxt, flags=re.IGNORECASE).strip()
                
                # Parantezleri temizle
                nxt = re.sub(r'\(\s*\|?', '', nxt).strip()
                
                if nxt and len(nxt) > 5:
                    addr_parts.append(nxt)
                    if '/' in nxt:  # Şehir bulundu
                        break
            
            if addr_parts:
                info['address'] = ' '.join(addr_parts)
        
        return info
    
    def _extract_company_name_by_position(self, image_path):
        """
        Konum bazlı OCR ile firma adını çıkar
        Birden fazla strateji ile farklı levha formatlarını destekler
        
        Args:
            image_path: Görüntü dosya yolu
            
        Returns:
            str: Firma ünvanı veya boş string
        """
        if not OCR_AVAILABLE or Output is None:
            return ''
        
        try:
            img = Image.open(image_path)
            
            logger.info('🔍 Firma adı arama başlıyor...')
            
            # Strateji 1: TİCARET ÜNVANI bazlı (mevcut)
            logger.debug('Strateji 1: TİCARET ÜNVANI bazlı arama')
            result = self._strategy_unvan_based(img)
            if result:
                logger.info(f'✅ Strateji 1 başarılı: {result[:50]}')
                return result
            logger.debug('Strateji 1 sonuç bulamadı')
            
            # Strateji 2: VERGİ DAİRESİ altında ara
            logger.debug('Strateji 2: Vergi dairesi altı arama')
            result = self._strategy_below_tax_office(img)
            if result:
                logger.info(f'✅ Strateji 2 başarılı: {result[:50]}')
                return result
            logger.debug('Strateji 2 sonuç bulamadı')
            
            # Strateji 3: Tüm metinden en uzun ŞİRKETİ/LİMİTED içeren satır
            logger.debug('Strateji 3: En uzun ŞİRKETİ satırı')
            result = self._strategy_longest_company_line(img)
            if result:
                logger.info(f'✅ Strateji 3 başarılı: {result[:50]}')
                return result
            logger.debug('Strateji 3 sonuç bulamadı')
            
            logger.warning('❌ Hiçbir strateji firma adı bulamadı')
            return ''
            
        except Exception as e:
            logger.error(f'Konum bazlı firma adı çıkarma hatası: {e}')
            return ''
    
    def _strategy_unvan_based(self, img):
        """Strateji 1: TİCARET ÜNVANI kelimesinin yanındaki metni al"""
        try:
            data = pytesseract.image_to_data(img, lang='tur', output_type=Output.DICT)
            
            # Kelime bazlı OCR
            data = pytesseract.image_to_data(img, lang='tur', output_type=Output.DICT)
            
            # ÜNVANI kelimesinin y pozisyonunu bul
            unvan_y = None
            unvan_x = None
            
            for i, word in enumerate(data['text']):
                if 'ÜNVAN' in word.upper():
                    unvan_y = data['top'][i]
                    unvan_x = data['left'][i]
                    break
            
            if not unvan_y:
                return ''
            
            # ÜNVANI'nın sağında ve altında (max 100px) olan kelimeleri topla
            company_words = []
            found_sirket = False
            
            for i, word in enumerate(data['text']):
                word_stripped = word.strip()
                if len(word_stripped) == 0:
                    continue
                
                y_pos = data['top'][i]
                x_pos = data['left'][i]
                y_diff = y_pos - unvan_y
                
                # ÜNVANI ile aynı hizada veya max 100px altında
                if 0 <= y_diff <= 100:
                    word_upper = word_stripped.upper()
                    
                    # ŞİRKETİ kelimesini bulduktan sonra dur (ama ŞİRKETİ'yi de ekle)
                    if 'ŞİRKET' in word_upper:
                        company_words.append({
                            'word': word_stripped,
                            'x': x_pos,
                            'y': y_pos,
                            'y_diff': y_diff,
                            'conf': int(data['conf'][i])
                        })
                        found_sirket = True
                        break
                    
                    # Stop kelimeleri - VERGİKİMLİK, NO, TC gibi
                    if any(stop in word_upper for stop in ['VERG', 'KİMLİK', 'KIMLIK', 'TC']):
                        continue
                    
                    # NO kelimesi - eğer sonraki kelime rakamsa dur
                    if word_upper == 'NO':
                        # Sonraki kelimeyi kontrol et
                        if i + 1 < len(data['text']):
                            next_word = data['text'][i + 1].strip()
                            if next_word.isdigit():
                                break
                        continue
                    
                    # ÜNVANI kelimesinin kendisini atla
                    if 'ÜNVAN' in word_upper:
                        continue
                    
                    # İŞ YERİ ADRESİ başlığını atla
                    if word_upper in ['İŞ', 'YERİ', 'ADRESİ'] and y_diff > 50:
                        continue
                    
                    # Güven skoru düşükse atla
                    conf = int(data['conf'][i])
                    if conf < 30:
                        continue
                    
                    # Sadece rakamlardan oluşuyorsa atla (vergi numarası olabilir)
                    if word_stripped.isdigit() and len(word_stripped) >= 9:
                        break
                    
                    company_words.append({
                        'word': word_stripped,
                        'x': x_pos,
                        'y': y_pos,
                        'y_diff': y_diff,
                        'conf': conf
                    })
            
            if not company_words:
                return ''
            
            # Y farkına göre sırala (önce aynı satır, sonra alt satır)
            # Sonra x pozisyonuna göre (soldan sağa)
            company_words.sort(key=lambda w: (w['y_diff'], w['x']))
            
            # Kelimeleri birleştir
            company_text = ' '.join([w['word'] for w in company_words])
            
            # Temizlik
            company_text = re.sub(r'\s+', ' ', company_text).strip()
            company_text = re.sub(r'[|!]', '', company_text).strip()
            
            # İŞ YERİ ADRESİ, TC KİMLİK gibi sonraki alanları kaldır
            stop_phrases = ['İŞ YERİ', 'TC KİMLİK', 'T.C.', 'VERGİ KİMLİK']
            for phrase in stop_phrases:
                if phrase in company_text.upper():
                    # Bu kelimeden öncesini al
                    parts = re.split(phrase, company_text, flags=re.IGNORECASE)
                    if parts[0]:
                        company_text = parts[0].strip()
            
            # Çok kısaysa alma
            if len(company_text) < 10:
                return ''
            
            # ŞİRKETİ, LİMİTED, A.Ş. gibi kelimeler yoksa muhtemelen firma adı değil
            company_keywords = ['ŞİRKET', 'LİMİTED', 'A.Ş', 'LTD', 'ANONİM', 'TİCARET', 'SANAYİ']
            if not any(kw in company_text.upper() for kw in company_keywords):
                return ''
            
            logger.info(f'Konum bazlı firma adı bulundu: {company_text}')
            return company_text
            
        except Exception as e:
            logger.error(f'Strateji 1 hatası: {e}')
            return ''
    
    def _strategy_below_tax_office(self, img):
        """Strateji 2: Vergi dairesi altındaki bölgede ŞİRKET içeren satırı bul"""
        try:
            text = pytesseract.image_to_string(img, lang='tur', config='--psm 6')
            lines = text.split('\n')
            
            # Vergi dairesi adını bul
            tax_office_idx = -1
            for i, line in enumerate(lines):
                # Büyük harfli tek kelime (ERTUĞRUL, OSMANGAZİ gibi)
                if line.strip().isupper() and len(line.strip()) > 5 and ' ' not in line.strip():
                    if not any(word in line.upper() for word in ['VERGİ', 'DAİRE', 'LEVHA']):
                        tax_office_idx = i
                        break
            
            if tax_office_idx == -1:
                return ''
            
            # Vergi dairesinden sonraki 10 satırda ŞİRKETİ/LİMİTED ara
            for i in range(tax_office_idx + 1, min(tax_office_idx + 10, len(lines))):
                line = lines[i].strip()
                line_upper = line.upper()
                
                if any(kw in line_upper for kw in ['ŞİRKET', 'LİMİTED', 'ANONİM']):
                    # Önceki satırları da dahil et (firma adı birden fazla satırda olabilir)
                    company_parts = []
                    for j in range(max(tax_office_idx + 1, i - 2), i + 1):
                        part = lines[j].strip()
                        if part and len(part) > 3:
                            # VERGİ, NO gibi kelimeleri atla
                            if not any(stop in part.upper() for stop in ['VERGİ', 'NO ', 'TC', 'KİMLİK']):
                                company_parts.append(part)
                    
                    company_text = ' '.join(company_parts)
                    company_text = re.sub(r'\s+', ' ', company_text).strip()
                    
                    if len(company_text) > 10:
                        logger.info(f'Strateji 2: {company_text}')
                        return company_text
            
            return ''
            
        except Exception as e:
            logger.debug(f'Strateji 2 hatası: {e}')
            return ''
    
    def _strategy_longest_company_line(self, img):
        """Strateji 3: Tüm metinden ŞİRKETİ/LİMİTED içeren en uzun satırı al"""
        try:
            text = pytesseract.image_to_string(img, lang='tur', config='--psm 6')
            lines = text.split('\n')
            
            candidates = []
            company_keywords = ['ŞİRKET', 'LİMİTED', 'A.Ş', 'LTD', 'ANONİM', 'SANAYİ', 'TİCARET']
            
            for line in lines:
                line_clean = line.strip()
                line_upper = line_clean.upper()
                
                # Şirket anahtar kelimesi içeren satırlar
                if any(kw in line_upper for kw in company_keywords):
                    # VERGİ KİMLİK öncesini al
                    if 'VERGİ' in line_upper and 'KİMLİK' in line_upper:
                        parts = re.split(r'VERGİ\s*KİMLİK', line_clean, flags=re.IGNORECASE)
                        line_clean = parts[0].strip()
                    
                    # NO ve rakamları temizle
                    line_clean = re.sub(r'NO\s+\d+', '', line_clean, flags=re.IGNORECASE)
                    
                    # Özel karakterleri temizle
                    line_clean = re.sub(r'[|!]', '', line_clean).strip()
                    line_clean = re.sub(r'\s+', ' ', line_clean)
                    
                    # ÜNVANI kelimesinden sonrasını al
                    if 'ÜNVAN' in line_clean.upper():
                        parts = re.split(r'ÜNVAN[İI]', line_clean, flags=re.IGNORECASE)
                        if len(parts) > 1:
                            line_clean = parts[-1].strip()
                    
                    if len(line_clean) > 15:
                        candidates.append(line_clean)
            
            if not candidates:
                return ''
            
            # En uzun olanı seç (genelde tam firma adı)
            best = max(candidates, key=len)
            
            # Son temizlik
            stop_phrases = ['İŞ YERİ', 'TC KİMLİK', 'T.C.', 'ADRESİ']
            for phrase in stop_phrases:
                if phrase in best.upper():
                    parts = re.split(phrase, best, flags=re.IGNORECASE)
                    best = parts[0].strip()
            
            if len(best) > 10:
                logger.info(f'Strateji 3: {best}')
                return best
            
            return ''
            
        except Exception as e:
            logger.debug(f'Strateji 3 hatası: {e}')
            return ''
    
    def extract_text_simple(self, pdf_path):
        """PDF'den tüm metni çıkar (basit versiyon)"""
        return self._extract_text_from_pdf(pdf_path)


if __name__ == '__main__':
    # Test
    reader = PDFReader()
    
    # Test için örnek bir vergi levhası PDF'i olmalı
    # test_pdf = 'test_vergi_levhasi.pdf'
    # info = reader.extract_tax_info(test_pdf)
    # print('Çıkarılan bilgiler:')
    # print(info)
    
    print('PDF Reader modülü hazır.')
    print('Gerçek test için vergi levhası PDF\'i gerekli.')
