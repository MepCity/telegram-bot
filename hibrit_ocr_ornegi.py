"""
Hibrit OCR entegrasyonu - bot.py'ye eklenecek kod örneği
"""

# ÜST KISIMDA IMPORT EKLE
from ai_ocr import AIVisionOCR
import os

class OfferBot:
    def __init__(self):
        self.excel_handler = ExcelHandler()
        self.pdf_reader = PDFReader()
        self.pdf_converter = PDFConverter()
        from document_handler import DocumentHandler
        self.document_handler = DocumentHandler()
        
        # AI OCR ekle (opsiyonel)
        self.use_ai_ocr = bool(os.getenv('OPENAI_API_KEY'))
        if self.use_ai_ocr:
            self.ai_ocr = AIVisionOCR(provider='openai')
            print('✅ AI OCR aktif (GPT-4 Vision)')
        else:
            print('ℹ️  Klasik OCR kullanılıyor (AI OCR için OPENAI_API_KEY ekleyin)')
        
        Path(config.TEMP_DIR).mkdir(exist_ok=True)
        Path(config.OUTPUT_DIR).mkdir(exist_ok=True)


    async def receive_tax_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Vergi levhası fotoğrafını işle - Hibrit OCR ile"""
        try:
            await update.message.reply_text("📸 Fotoğraf alındı, işleniyor...")
            
            # Fotoğrafı indir
            photo = await update.message.photo[-1].get_file()
            photo_path = Path(f'temp/tax_photo_{update.effective_user.id}.jpg')
            photo_path.parent.mkdir(exist_ok=True)
            await photo.download_to_drive(photo_path)
            
            # HIBRIT YAKLAŞIM
            tax_data = None
            
            # 1. Önce klasik OCR dene (ücretsiz, hızlı)
            await update.message.reply_text("🔍 Klasik OCR ile okunuyor...")
            tax_data = self.pdf_reader.extract_from_image(str(photo_path))
            
            # 2. Firma adı boşsa veya çok kısaysa AI kullan
            if self.use_ai_ocr:
                company_name = tax_data.get('company_name', '')
                
                # AI gerekli mi?
                needs_ai = (
                    not company_name or 
                    len(company_name) < 15 or
                    not any(kw in company_name.upper() for kw in ['ŞİRKET', 'LİMİTED', 'A.Ş'])
                )
                
                if needs_ai:
                    await update.message.reply_text("🤖 AI OCR devreye giriyor...")
                    ai_result = self.ai_ocr.extract_tax_info(str(photo_path))
                    
                    # AI sonucu daha iyiyse kullan
                    if ai_result.get('company_name') and len(ai_result['company_name']) > len(company_name):
                        tax_data = ai_result
                        await update.message.reply_text("✨ AI OCR kullanıldı")
            
            context.user_data['customer_name'] = tax_data.get('company_name', 'Firma Adı Belirtilmedi')
            context.user_data['tax_data'] = tax_data
            
            # Sonuçları göster
            company_icon = "✅" if tax_data.get('company_name') else "⚠️"
            office_icon = "✅" if tax_data.get('tax_office') else "⚠️"
            
            await update.message.reply_text(
                f"{company_icon} Firma: {tax_data.get('company_name', 'Okunamadı')[:50]}...\n"
                f"{office_icon} Vergi Dairesi: {tax_data.get('tax_office', 'Okunamadı')}",
                parse_mode='Markdown'
            )
            
            photo_path.unlink(missing_ok=True)
            
            # Vergi numarası kontrolü
            tax_num = tax_data.get('tax_number', '')
            if not tax_num:
                await update.message.reply_text(
                    "📝 *Vergi Numarası:*\n\n"
                    "Fotoğraftan vergi numarası okunamadı.\n"
                    "Lütfen 10 haneli vergi numarasını yazın:",
                    parse_mode='Markdown'
                )
                return ASK_TAX_NUMBER
            elif len(tax_num) == 9:
                context.user_data['tax_data']['partial_tax_number'] = tax_num
                await update.message.reply_text(
                    f"📝 *Vergi Numarası (son hane eksik):*\n\n"
                    f"Okunan: {tax_num} (9 hane)\n\n"
                    f"Lütfen sadece *son 1 haneyi* yazın:\n"
                    f"(Tam vergi no: {tax_num}_)",
                    parse_mode='Markdown'
                )
                return ASK_TAX_NUMBER
            elif len(tax_num) != 10:
                await update.message.reply_text(
                    f"⚠️ Vergi numarası hatalı okundu ({len(tax_num)} hane).\n"
                    f"Lütfen 10 haneli vergi numarasını yazın:",
                    parse_mode='Markdown'
                )
                return ASK_TAX_NUMBER
                
        except Exception as e:
            logger.error(f'Fotoğraf okuma hatası: {e}')
            await update.message.reply_text("❌ Fotoğraf okunamadı. Lütfen PDF olarak yükleyin.")
            return ASK_TAX_PDF
        
        await update.message.reply_text(config.MESSAGES['ask_contact_person'], parse_mode='Markdown')
        return ASK_CONTACT_PERSON
