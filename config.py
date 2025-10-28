"""
Konfigürasyon ayarları
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Google Gemini Vision (ÜCRETSİZ OCR)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# Şirket Bilgileri
COMPANY_NAME = os.getenv('COMPANY_NAME', 'İSKELE PATENT & DANIŞMANLIK')
COMPANY_ADDRESS = os.getenv('COMPANY_ADDRESS', '')
COMPANY_PHONE = os.getenv('COMPANY_PHONE', '')
COMPANY_EMAIL = os.getenv('COMPANY_EMAIL', '')
COMPANY_WEBSITE = os.getenv('COMPANY_WEBSITE', '')

# Teklif Ayarları
OFFER_VALIDITY_DAYS = int(os.getenv('OFFER_VALIDITY_DAYS', '30'))
DEFAULT_PAYMENT_METHOD = os.getenv('DEFAULT_PAYMENT_METHOD', 'PEŞİN')
KDV_RATE = float(os.getenv('KDV_RATE', '0.20'))  # %20 KDV

# Dosya Yolları
TEMPLATE_PATH = 'yeni.xlsx'  # YENİ ÖZEL ŞABLON (28.10.2025)
OUTPUT_DIR = 'outputs'
TEMP_DIR = 'temp'

# Bot mesajları
MESSAGES = {
    'start': """
🤖 *Teklif Oluşturma Botu*

Merhaba! Size otomatik teklif oluşturmada yardımcı olacağım.

İşlem adımları:
1️⃣ Vergi levhası (PDF) - Firma bilgileri otomatik çıkarılır
2️⃣ Yetkili kişi adı
3️⃣ Ürün/Hizmet bilgileri (ad, adet, fiyat)
4️⃣ Teklif Excel dosyası oluşturulur (%25 KDV ile)

Başlamak için /yeni yazın.
    """,
    'ask_tax_pdf': "📄 *Vergi Levhası:*\n\nLütfen müşteri firmanın vergi levhasını PDF olarak gönderin.\n\nFirma bilgileri otomatik olarak çıkarılacak.\n\n(İptal etmek için /iptal yazın)",
    'ask_contact_person': "👤 *Firma Yetkilisi:*\n\nTeklif için firma yetkilisinin adını yazın:\n\n(Örnek: Ahmet Bey)",
    'ask_offer_date': "📅 *Teklif Tarihi:*\n\nTeklif tarihi otomatik olarak bugünün tarihi olsun mu?\n\n(Evet yazarsanız otomatik, Hayır yazarsanız manuel girebilirsiniz)",
    'ask_manual_date': "📅 *Teklif Tarihi:*\n\nLütfen teklif tarihini girin:\n\n(Örnek: 28.10.2025)",
    'ask_email': "📧 *E-posta Adresi:*\n\nFirmanın iletişim e-posta adresini yazın:\n\n(Örnek: info@sirket.com.tr)",
    'ask_service_name': "📦 *Hizmet/Ürün Adı:*\n\nTeklif yapılacak hizmet/ürünün adını yazın:\n\n(Örnek: YATIRIM TEŞVİK BELGESİ)",
    'ask_quantity': "🔢 *Adet/Miktar:*\n\nHizmet/ürün miktarını yazın:\n\n(Örnek: 1)",
    'ask_unit_price': "💰 *Birim Fiyat (TL):*\n\nBirim fiyatı TL olarak yazın:\n\n(Örnek: 750000)",
    'ask_add_more': "➕ *Başka Ürün/Hizmet Eklemek İster misiniz?*",
    'processing': "⏳ Teklif hazırlanıyor...\n\n� Hesaplamalar yapılıyor (KDV ekleniyor)...",
    'success': """
✅ *Teklif başarıyla oluşturuldu!*

📊 Özet:
• Ara Toplam: {subtotal:,.2f} TL
• KDV (%25): {kdv:,.2f} TL  
• *Genel Toplam: {total:,.2f} TL*

Yeni teklif için /yeni yazın.
    """,
    'error': "❌ Bir hata oluştu: {error}\n\nTekrar denemek için /yeni yazın.",
    'cancelled': "🚫 İşlem iptal edildi.\n\nYeni teklif için /yeni yazın.",
    'pdf_read_success': """
✅ *Vergi levhası okundu!*

🏢 *Firma:* {company_name}

Devam ediyoruz...
    """,
    'pdf_read_error': "⚠️ Vergi levhası okunamadı, ancak devam ediyoruz.\n\nFirma adını manuel girebilirsiniz.",
}
