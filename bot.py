"""
Telegram Bot - Otomatik Teklif Oluşturma
"""
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from pathlib import Path
from datetime import datetime
import config
from excel_handler import ExcelHandler
from pdf_reader import PDFReader
from pdf_converter import PDFConverter
from gemini_ocr import GeminiOCR
from email_sender import EmailSender

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation states - Manuel giriş, sözleşme ve email için state'ler
(ASK_INITIAL_CHOICE, ASK_TAX_PDF, ASK_TAX_NUMBER, ASK_CONTACT_PERSON, ASK_OFFER_DATE, ASK_MANUAL_DATE, 
 ASK_EMAIL, ASK_SERVICE_NAME, ASK_QUANTITY, ASK_UNIT_PRICE, ASK_ADD_MORE,
 ASK_MANUAL_ENTRY, ASK_MANUAL_COMPANY, ASK_MANUAL_TAX_OFFICE, ASK_MANUAL_TAX_NUMBER, ASK_MANUAL_ADDRESS,
 ASK_NOTES_CHOICE, ASK_NOTES_TEXT, ASK_PROJECT_TYPE, ASK_CONTRACT_AMOUNT, ASK_SEND_EMAIL, ASK_EMAIL_FOR_SENDING,
 ASK_DELIVERY_DATE_CHOICE, ASK_DELIVERY_DATE) = range(24)

class OfferBot:
    def __init__(self):
        self.excel_handler = ExcelHandler()
        self.pdf_reader = PDFReader()
        self.pdf_converter = PDFConverter()
        
        # Gemini OCR'ı başlat (varsa)
        try:
            self.gemini_ocr = GeminiOCR(api_key=config.GEMINI_API_KEY)
            logger.info('✅ Gemini Vision OCR aktif')
        except Exception as e:
            self.gemini_ocr = None
            logger.warning(f'⚠️ Gemini OCR başlatılamadı: {e}')
        
        from document_handler import DocumentHandler
        self.document_handler = DocumentHandler()
        
        # Email sender'ı başlat
        self.email_sender = EmailSender()
        logger.info(f'📧 Email durumu: {"Aktif" if self.email_sender.enabled else "Devre dışı"}')
        
        Path(config.TEMP_DIR).mkdir(exist_ok=True)
        Path(config.OUTPUT_DIR).mkdir(exist_ok=True)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(config.MESSAGES['start'], parse_mode='Markdown')
        return ConversationHandler.END
    
    async def new_offer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Başlangıç seçim ekranı: Kullanıcıdan işlem türünü sor
        context.user_data.clear()
        context.user_data['services'] = []
        keyboard = [['YTB Teklifi', 'Proje']]
        await update.message.reply_text(
            "Hangi işlemi yapmak istiyorsunuz?\n\n• YTB Teklifi: Yatırım Teşvik Belgesi teklif dosyalarını oluşturur\n• Proje: Sadece sözleşme belgesini oluşturur",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return ASK_INITIAL_CHOICE

    async def receive_initial_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Kullanıcının başlangıç seçiminden sonra akışı başlat"""
        choice = update.message.text.strip().lower()
        if choice in ['ytb teklif', 'ytb teklifi', 'ytb']:
            context.user_data['initial_choice'] = 'YTB'
        else:
            context.user_data['initial_choice'] = 'PROJE'

        # Ardından normal veri toplama akışına devam et (vergi levhası sor)
        await update.message.reply_text(config.MESSAGES['ask_tax_pdf'], reply_markup=ReplyKeyboardRemove(), parse_mode='Markdown')
        return ASK_TAX_PDF
    
    async def receive_tax_pdf(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message.document:
            await update.message.reply_text("❌ Lütfen bir PDF dosyası gönderin.")
            return ASK_TAX_PDF
        
        file = await update.message.document.get_file()
        temp_dir = Path(config.TEMP_DIR)
        pdf_path = temp_dir / f'tax_{update.message.from_user.id}.pdf'
        await file.download_to_drive(pdf_path)
        await update.message.reply_text("⏳ Vergi levhası okunuyor...")
        
        try:
            # Önce Gemini Vision ile dene (daha doğru)
            if self.gemini_ocr:
                logger.info('🤖 Gemini Vision ile PDF okuma deneniyor...')
                await update.message.reply_text("🤖 Gemini AI ile analiz ediliyor...")
                tax_info = self.gemini_ocr.extract_tax_info_from_pdf(str(pdf_path))
                
                # Gemini başarısızsa Tesseract'e düş
                if not tax_info.get('company_name'):
                    logger.warning('⚠️ Gemini okuamadı, Tesseract deneniyor...')
                    await update.message.reply_text("🔄 Alternatif yöntemle deneniyor...")
                    tax_info = self.pdf_reader.extract_tax_info(str(pdf_path))
            else:
                # Gemini yoksa direkt Tesseract
                tax_info = self.pdf_reader.extract_tax_info(str(pdf_path))
            
            company_name = tax_info.get('company_name', '')
            
            # Tax data'yı context'e kaydet (document_handler için)
            context.user_data['tax_data'] = tax_info
            
            if company_name:
                context.user_data['customer_name'] = company_name
                await update.message.reply_text(config.MESSAGES['pdf_read_success'].format(company_name=company_name), parse_mode='Markdown')
            else:
                await update.message.reply_text(config.MESSAGES['pdf_read_error'])
                context.user_data['customer_name'] = 'Firma Adı Belirtilmedi'
        except Exception as e:
            logger.error(f'PDF okuma hatası: {e}')
            await update.message.reply_text(config.MESSAGES['pdf_read_error'])
            context.user_data['customer_name'] = 'Firma Adı Belirtilmedi'
            context.user_data['tax_data'] = {}
        
        pdf_path.unlink(missing_ok=True)
        
        # Vergi numarası kontrolü - eğer boşsa sor
        if not context.user_data.get('tax_data', {}).get('tax_number'):
            await update.message.reply_text(
                "📝 *Vergi Numarası:*\n\n"
                "Vergi levhasından vergi numarası otomatik okunamadı.\n"
                "Lütfen 10 haneli vergi numarasını yazın:",
                parse_mode='Markdown'
            )
            return ASK_TAX_NUMBER
        
        await update.message.reply_text(config.MESSAGES['ask_contact_person'], parse_mode='Markdown')
        return ASK_CONTACT_PERSON
    
    async def receive_tax_number(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        tax_number = update.message.text.strip()
        # Sadece rakamları al
        tax_number = ''.join(filter(str.isdigit, tax_number))
        
        if len(tax_number) != 10:
            await update.message.reply_text(
                "❌ Vergi numarası 10 haneli olmalıdır. Lütfen tekrar girin:",
                parse_mode='Markdown'
            )
            return ASK_TAX_NUMBER
        
        # tax_data'ya ekle
        if 'tax_data' not in context.user_data:
            context.user_data['tax_data'] = {}
        context.user_data['tax_data']['tax_number'] = tax_number
        
        await update.message.reply_text(f"✅ Vergi numarası kaydedildi: {tax_number}")
        await update.message.reply_text(config.MESSAGES['ask_contact_person'], parse_mode='Markdown')
        return ASK_CONTACT_PERSON
    
    async def receive_tax_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Vergi levhası fotoğrafını işle - SADECE GEMINI VISION"""
        try:
            await update.message.reply_text("📸 Fotoğraf alındı, AI Vision ile okunuyor...")
            
            # Fotoğrafı indir
            photo = await update.message.photo[-1].get_file()
            photo_path = Path(f'temp/tax_photo_{update.effective_user.id}.jpg')
            photo_path.parent.mkdir(exist_ok=True)
            await photo.download_to_drive(photo_path)
            
            # 🤖 SADECE GEMİNI VISION KULLAN
            tax_data = None
            gemini_success = False
            
            if self.gemini_ocr:
                try:
                    await update.message.reply_text("🤖 Google Gemini Vision ile analiz ediliyor...")
                    tax_data = self.gemini_ocr.extract_tax_info(str(photo_path))
                    
                    # Başarılı mı kontrol et (tüm alanlar dolu mu?)
                    if (tax_data.get('company_name') and 
                        tax_data.get('tax_office') and 
                        tax_data.get('tax_number') and 
                        len(tax_data.get('tax_number', '')) == 10):
                        
                        gemini_success = True
                        await update.message.reply_text("✅ AI Vision ile başarıyla okundu!")
                        
                except Exception as e:
                    logger.error(f'Gemini okuma hatası: {e}')
                    gemini_success = False
            else:
                await update.message.reply_text("❌ AI Vision mevcut değil (API key eksik)")
            
            photo_path.unlink(missing_ok=True)
            
            # ❌ GEMİNİ BAŞARISIZ OLURSA MANUEL GİRİŞ TEKLİF ET
            if not gemini_success:
                keyboard = [['Evet, manuel gireceğim', 'Hayır, iptal et']]
                await update.message.reply_text(
                    "⚠️ *Fotoğraf otomatik okunamadı.*\n\n"
                    "📝 Tüm bilgileri *manuel olarak* girmek ister misiniz?\n\n"
                    "Manuel giriş yaparsanız şu bilgileri tek tek soracağım:\n"
                    "• Firma Ünvanı\n"
                    "• Vergi Dairesi\n"
                    "• Vergi Numarası (10 hane)\n"
                    "• Adres",
                    reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
                    parse_mode='Markdown'
                )
                return ASK_MANUAL_ENTRY
            
            # ✅ GEMİNİ BAŞARILI - Bilgileri kaydet
            context.user_data['customer_name'] = tax_data.get('company_name', 'Firma Adı Belirtilmedi')
            context.user_data['tax_data'] = tax_data
            
            await update.message.reply_text(
                f"✅ *Bilgiler başarıyla okundu:*\n\n"
                f"📋 *Firma:* {tax_data.get('company_name', 'Okunamadı')}\n"
                f"🏢 *Vergi Dairesi:* {tax_data.get('tax_office', 'Okunamadı')}\n"
                f"🔢 *Vergi No:* {tax_data.get('tax_number', 'Okunamadı')}\n"
                f"📍 *Adres:* {tax_data.get('address', 'Okunamadı')[:50]}...",
                parse_mode='Markdown'
            )
                
        except Exception as e:
            logger.error(f'Fotoğraf okuma hatası: {e}')
            await update.message.reply_text(
                f"❌ Bir hata oluştu: {str(e)}\n\n"
                "Lütfen tekrar deneyin veya PDF olarak yükleyin."
            )
            return ASK_TAX_PDF
        
        await update.message.reply_text(config.MESSAGES['ask_contact_person'], parse_mode='Markdown')
        return ASK_CONTACT_PERSON
    
    async def ask_manual_entry_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manuel giriş yapılacak mı?"""
        response = update.message.text.strip()
        
        if 'evet' in response.lower() or 'manuel' in response.lower():
            # Manuel girişe başla
            await update.message.reply_text(
                "📝 *Manuel Veri Girişi Başlıyor*\n\n"
                "1️⃣ Firma ünvanını yazın:\n"
                "(Örnek: ABC TİCARET LİMİTED ŞİRKETİ)",
                reply_markup=ReplyKeyboardRemove(),
                parse_mode='Markdown'
            )
            return ASK_MANUAL_COMPANY
        else:
            # İptal et
            await update.message.reply_text(
                "❌ İşlem iptal edildi.\n\n"
                "/yeni_teklif komutu ile yeni bir teklif başlatabilirsiniz.",
                reply_markup=ReplyKeyboardRemove()
            )
            return ConversationHandler.END
    
    async def receive_manual_company(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manuel firma adı"""
        company_name = update.message.text.strip()
        
        if len(company_name) < 3:
            await update.message.reply_text(
                "⚠️ Firma adı çok kısa. Lütfen tam ünvanı yazın:"
            )
            return ASK_MANUAL_COMPANY
        
        context.user_data['customer_name'] = company_name
        if 'tax_data' not in context.user_data:
            context.user_data['tax_data'] = {}
        context.user_data['tax_data']['company_name'] = company_name
        
        await update.message.reply_text(
            f"✅ Firma: {company_name}\n\n"
            "2️⃣ Vergi dairesini yazın:\n"
            "(Örnek: ÇANKAYA)",
            parse_mode='Markdown'
        )
        return ASK_MANUAL_TAX_OFFICE
    
    async def receive_manual_tax_office(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manuel vergi dairesi"""
        tax_office = update.message.text.strip().upper()
        
        if len(tax_office) < 2:
            await update.message.reply_text(
                "⚠️ Vergi dairesi adı çok kısa. Lütfen tekrar yazın:"
            )
            return ASK_MANUAL_TAX_OFFICE
        
        context.user_data['tax_data']['tax_office'] = tax_office
        
        await update.message.reply_text(
            f"✅ Vergi Dairesi: {tax_office}\n\n"
            "3️⃣ 10 haneli vergi numarasını yazın:\n"
            "(Sadece rakam, boşluk yok)",
            parse_mode='Markdown'
        )
        return ASK_MANUAL_TAX_NUMBER
    
    async def receive_manual_tax_number(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manuel vergi numarası"""
        tax_number = update.message.text.strip().replace(' ', '').replace('-', '')
        
        # Sadece rakam kontrolü
        if not tax_number.isdigit():
            await update.message.reply_text(
                "⚠️ Vergi numarası sadece rakamlardan oluşmalı.\n"
                "Lütfen tekrar yazın:"
            )
            return ASK_MANUAL_TAX_NUMBER
        
        # 10 hane kontrolü
        if len(tax_number) != 10:
            await update.message.reply_text(
                f"⚠️ Vergi numarası 10 hane olmalı (şu an {len(tax_number)} hane).\n"
                "Lütfen tekrar yazın:"
            )
            return ASK_MANUAL_TAX_NUMBER
        
        context.user_data['tax_data']['tax_number'] = tax_number
        
        await update.message.reply_text(
            f"✅ Vergi No: {tax_number}\n\n"
            "4️⃣ Firma adresini yazın:",
            parse_mode='Markdown'
        )
        return ASK_MANUAL_ADDRESS
    
    async def receive_manual_address(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manuel adres - Son adım"""
        address = update.message.text.strip()
        
        if len(address) < 5:
            await update.message.reply_text(
                "⚠️ Adres çok kısa. Lütfen tam adresi yazın:"
            )
            return ASK_MANUAL_ADDRESS
        
        context.user_data['tax_data']['address'] = address
        
        # Özet göster
        await update.message.reply_text(
            "✅ *Tüm bilgiler kaydedildi:*\n\n"
            f"📋 *Firma:* {context.user_data['tax_data']['company_name']}\n"
            f"🏢 *Vergi Dairesi:* {context.user_data['tax_data']['tax_office']}\n"
            f"🔢 *Vergi No:* {context.user_data['tax_data']['tax_number']}\n"
            f"📍 *Adres:* {address[:50]}...",
            parse_mode='Markdown'
        )
        
        await update.message.reply_text(config.MESSAGES['ask_contact_person'], parse_mode='Markdown')
        return ASK_CONTACT_PERSON
    
    async def receive_contact_person(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['contact_person'] = update.message.text.strip()
        keyboard = [['Evet', 'Hayır']]
        await update.message.reply_text(
            config.MESSAGES['ask_offer_date'], 
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True),
            parse_mode='Markdown'
        )
        return ASK_OFFER_DATE
    
    async def receive_offer_date_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        choice = update.message.text.strip().lower()
        if choice in ['evet', 'e']:
            # Otomatik bugünün tarihi
            context.user_data['offer_date'] = datetime.now().strftime('%d.%m.%Y')
            await update.message.reply_text(
                f"✅ Teklif tarihi: {context.user_data['offer_date']}",
                reply_markup=ReplyKeyboardRemove()
            )
            await update.message.reply_text(config.MESSAGES['ask_email'], parse_mode='Markdown')
            return ASK_EMAIL
        else:
            # Manuel tarih girişi
            await update.message.reply_text(
                config.MESSAGES['ask_manual_date'],
                reply_markup=ReplyKeyboardRemove(),
                parse_mode='Markdown'
            )
            return ASK_MANUAL_DATE
    
    async def receive_manual_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['offer_date'] = update.message.text.strip()
        await update.message.reply_text(config.MESSAGES['ask_email'], parse_mode='Markdown')
        return ASK_EMAIL
    
    async def receive_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        email = update.message.text.strip()
        context.user_data['email'] = email
        await update.message.reply_text(f"✅ E-posta: {email}")
        
        # YTB seçildiyse hizmet sorularına geç, PROJE seçildiyse direkt proje türüne geç
        if context.user_data.get('initial_choice') == 'YTB':
            await update.message.reply_text(config.MESSAGES['ask_service_name'], parse_mode='Markdown')
            return ASK_SERVICE_NAME
        else:
            # PROJE seçildiyse direkt proje türünü sor
            return await self.ask_project_type(update, context)
    
    async def receive_service_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['current_service'] = {'name': update.message.text.strip()}
        await update.message.reply_text(config.MESSAGES['ask_quantity'], parse_mode='Markdown')
        return ASK_QUANTITY
    
    async def receive_quantity(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            quantity = int(update.message.text.strip())
            context.user_data['current_service']['quantity'] = quantity
            await update.message.reply_text(config.MESSAGES['ask_unit_price'], parse_mode='Markdown')
            return ASK_UNIT_PRICE
        except ValueError:
            await update.message.reply_text("❌ Geçersiz miktar. Lütfen sayı girin:")
            return ASK_QUANTITY
    
    async def receive_unit_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            price_text = update.message.text.strip().replace('.', '').replace(',', '.')
            unit_price = float(price_text)
            context.user_data['current_service']['unit_price'] = unit_price
            context.user_data['services'].append(context.user_data['current_service'])
            context.user_data.pop('current_service')
            
            subtotal = sum(s['quantity'] * s['unit_price'] for s in context.user_data['services'])
            await update.message.reply_text(f"✅ Eklendi!\nAra Toplam: {subtotal:,.2f} TL", parse_mode='Markdown')
            
            keyboard = [['Evet', 'Hayır']]
            await update.message.reply_text(config.MESSAGES['ask_add_more'], reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
            return ASK_ADD_MORE
        except ValueError:
            await update.message.reply_text("❌ Geçersiz fiyat. Sayı girin:")
            return ASK_UNIT_PRICE
    
    async def ask_add_more(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.text.strip().lower() in ['evet', 'e']:
            await update.message.reply_text(config.MESSAGES['ask_service_name'], reply_markup=ReplyKeyboardRemove(), parse_mode='Markdown')
            return ASK_SERVICE_NAME
        
        # Ürün ekleme bitti, şimdi not eklemek isteyip istemediğini sor
        keyboard = [['Evet', 'Hayır']]
        await update.message.reply_text(
            "📝 Teklife özel not eklemek ister misiniz?\n\n"
            "(Not alanı A18 hücresinde görünecektir)",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        )
        return ASK_NOTES_CHOICE
    
    async def receive_notes_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Not eklenip eklenmeyeceğine karar ver"""
        if update.message.text.strip().lower() in ['evet', 'e']:
            await update.message.reply_text(
                "📝 Lütfen teklife eklemek istediğiniz notu yazın:\n\n"
                "(Örn: 'Fiyatlara KDV dahildir', 'Ödemeler 30 gün içinde yapılmalıdır', vb.)",
                reply_markup=ReplyKeyboardRemove()
            )
            return ASK_NOTES_TEXT
        else:
            # Not istemiyorsa boş not ile devam et
            context.user_data['notes'] = ''
            # Teslim tarihi sorusuna geç
            keyboard = [['Evet', 'Hayır']]
            await update.message.reply_text(
                "📅 Planlanan teslim tarihi girilsin mi?\n\n"
                "(Excel'de H12 hücresinde görünecektir)",
                reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            )
            return ASK_DELIVERY_DATE_CHOICE
    
    async def receive_notes_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Kullanıcının yazdığı notu kaydet"""
        notes_text = update.message.text.strip()
        context.user_data['notes'] = notes_text
        await update.message.reply_text(f"✅ Not eklendi:\n\n{notes_text}")
        
        # Teslim tarihi sorusuna geç
        keyboard = [['Evet', 'Hayır']]
        await update.message.reply_text(
            "📅 Planlanan teslim tarihi girilsin mi?\n\n"
            "(Excel'de H12 hücresinde görünecektir)",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        )
        return ASK_DELIVERY_DATE_CHOICE
    
    async def receive_delivery_date_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Teslim tarihi girilip girilmeyeceğine karar ver"""
        if update.message.text.strip().lower() in ['evet', 'e']:
            await update.message.reply_text(
                "📅 Planlanan teslim tarihini yazın:\n\n"
                "Örnekler:\n"
                "• 15.11.2025\n"
                "• 30 gün içinde\n"
                "• Sözleşme imzalandıktan sonra 2 hafta içinde\n"
                "• ----",
                reply_markup=ReplyKeyboardRemove()
            )
            return ASK_DELIVERY_DATE
        else:
            # Teslim tarihi istemiyorsa boş bırak
            context.user_data['delivery_date'] = ''
            # YTB ise direkt belge oluştur, PROJE ise sözleşme bilgilerini sor
            if context.user_data.get('initial_choice') == 'PROJE':
                return await self.ask_project_type(update, context)
            else:
                # YTB seçilmişse direkt belge oluşturmaya geç
                await update.message.reply_text(config.MESSAGES['processing'], reply_markup=ReplyKeyboardRemove(), parse_mode='Markdown')
                return await self.generate_documents(update, context)
    
    async def receive_delivery_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Kullanıcının yazdığı teslim tarihini kaydet"""
        delivery_date = update.message.text.strip()
        context.user_data['delivery_date'] = delivery_date
        await update.message.reply_text(f"✅ Planlanan teslim tarihi: {delivery_date}")
        
        # YTB ise direkt belge oluştur, PROJE ise sözleşme bilgilerini sor
        if context.user_data.get('initial_choice') == 'PROJE':
            return await self.ask_project_type(update, context)
        else:
            # YTB seçilmişse direkt belge oluşturmaya geç
            await update.message.reply_text(config.MESSAGES['processing'], reply_markup=ReplyKeyboardRemove(), parse_mode='Markdown')
            return await self.generate_documents(update, context)
    
    async def ask_project_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Sözleşme için proje türünü sor"""
        await update.message.reply_text(
            "📋 *4. Belge: Sözleşme*\n\n"
            "Proje türünü yazın:\n"
            "(Örnek: TÜBİTAK 1501 PROJESİ, KOSGEB PROJE DANIŞMANLIĞI, vb.)\n\n"
            "ℹ️ Sözleşmede büyük harfle yazılacak.",
            parse_mode='Markdown'
        )
        return ASK_PROJECT_TYPE
    
    async def receive_project_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Proje türünü kaydet ve sözleşme bedelini sor"""
        proje_turu = update.message.text.strip()
        context.user_data['proje_turu'] = proje_turu
        
        await update.message.reply_text(
            f"✅ Proje türü: {proje_turu.upper()}\n\n"
            "💰 Sözleşme bedelini yazın:\n\n"
            "Örnekler:\n"
            "• 80.000 TL'nin %5'i\n"
            "• 100.000 %5\n"
            "• 5.000 TL\n"
            "• 10000\n\n"
            "ℹ️ Hem sabit tutar hem de yüzde hesaplamaları desteklenir.",
            parse_mode='Markdown'
        )
        return ASK_CONTRACT_AMOUNT
    
    async def receive_contract_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Sözleşme bedelini al ve parse et"""
        user_input = update.message.text.strip()
        
        try:
            # Ücret bilgilerini parse et
            ucret_bilgisi = self.parse_contract_amount(user_input)
            context.user_data['ucret_bilgisi'] = ucret_bilgisi
            
            await update.message.reply_text(
                f"✅ Sözleşme bedeli kaydedildi:\n"
                f"• Tutar: {ucret_bilgisi['tutar']}\n"
                f"• Açıklama: {ucret_bilgisi['aciklama']}\n\n"
                "📄 Belgeler hazırlanıyor...",
                parse_mode='Markdown'
            )
            
            # Belgeleri oluştur
            return await self.generate_documents(update, context)
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ Hata: {e}\n\n"
                "Lütfen formatı kontrol edip tekrar deneyin.\n\n"
                "Örnekler:\n"
                "• 80.000 TL'nin %5'i\n"
                "• 100.000 %5\n"
                "• 5.000 TL\n"
                "• 10000",
                parse_mode='Markdown'
            )
            return ASK_CONTRACT_AMOUNT
    
    def parse_contract_amount(self, user_input):
        """
        Kullanıcı girdisinden sözleşme bedeli bilgisini parse eder.
        
        Örnekler:
        - "80.000 TL'nin %5'i" → {'tutar': '80.000', 'aciklama': "%5'i"}
        - "50000 TL nin %10 u" → {'tutar': '50.000', 'aciklama': '%10'u'}
        - "5.000 TL" → {'tutar': '5.000', 'aciklama': 'sabit tutar'}
        - "10000" → {'tutar': '10.000', 'aciklama': 'sabit tutar'}
        """
        import re
        
        # Normalize et (Türkçe karakterleri koru)
        text = user_input.strip()
        
        # Pattern 1: "80.000 TL'nin %5'i" formatı
        pattern1 = r"([\d.,]+)\s*TL['\']?\s*n[iıİI]n?\s*(%\d+)['\']?[iıİI]?"
        match = re.search(pattern1, text, re.IGNORECASE)
        
        if match:
            tutar_str = match.group(1).replace('.', '').replace(',', '.')
            yuzde = match.group(2)
            
            # Formatla
            try:
                tutar = float(tutar_str)
                formatted_tutar = f"{tutar:,.0f}".replace(',', '.')
                aciklama = f"{yuzde}'i"
                
                return {
                    'tutar': formatted_tutar,
                    'aciklama': aciklama
                }
            except:
                pass
        
        # Pattern 2: "100.000 %5" formatı (TL'nin kelimesi yok)
        pattern2 = r"([\d.,]+)\s+(%\d+)"
        match = re.search(pattern2, text, re.IGNORECASE)
        
        if match:
            tutar_str = match.group(1).replace('.', '').replace(',', '.')
            yuzde = match.group(2)
            
            try:
                tutar = float(tutar_str)
                formatted_tutar = f"{tutar:,.0f}".replace(',', '.')
                aciklama = f"{yuzde}'i"
                
                return {
                    'tutar': formatted_tutar,
                    'aciklama': aciklama
                }
            except:
                pass
        
        # Pattern 3: Sadece rakam veya "5.000 TL" formatı
        pattern3 = r"([\d.,]+)"
        match = re.search(pattern3, text)
        
        if match:
            tutar_str = match.group(1).replace('.', '').replace(',', '.')
            try:
                tutar = float(tutar_str)
                formatted_tutar = f"{tutar:,.0f}".replace(',', '.')
                
                return {
                    'tutar': formatted_tutar,
                    'aciklama': 'sabit tutar'
                }
            except:
                pass
        
        raise ValueError("Geçersiz format")

    
    async def generate_documents(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Belge oluşturma işlemini gerçekleştir (YTB veya Proje)"""
        try:
            # Müşteri verileri
            customer_data = {
                'name': context.user_data.get('customer_name', ''), 
                'contact_person': context.user_data.get('contact_person', ''),
                'tax_office': context.user_data.get('tax_data', {}).get('tax_office', ''),
                'tax_number': context.user_data.get('tax_data', {}).get('tax_number', ''),
                'address': context.user_data.get('tax_data', {}).get('address', '')
            }
            
            services = context.user_data.get('services', [])
            
            # Teklif bilgileri (yeni format)
            from datetime import timedelta
            offer_date = context.user_data.get('offer_date', datetime.now().strftime('%d.%m.%Y'))
            validity_date = (datetime.now() + timedelta(days=config.OFFER_VALIDITY_DAYS)).strftime('%d.%m.%Y')
            
            offer_info = {
                'offer_date': offer_date,
                'subject': context.user_data.get('subject', ''),  # Konu (opsiyonel)
                'validity': validity_date,  # Son geçerlilik
                'currency': '₺',  # Para birimi (₺, $, €)
                'discount_rate': 0,  # İskonto oranı (varsayılan 0)
                'notes': context.user_data.get('notes', ''),  # Kullanıcının eklediği not
                'delivery_date': context.user_data.get('delivery_date', '')  # Planlanan teslim tarihi
            }
            
            pdf_files = []
            tax_data = context.user_data.get('tax_data', {})
            email = context.user_data.get('email', '')

            # Eğer kullanıcı YTB Teklifi seçtiyse YTB ile ilgili 3 belgeyi oluştur
            if context.user_data.get('initial_choice') == 'YTB':
                # 1. YTB Teklif Excel'i oluştur
                await update.message.reply_text("📄 1/4 - Teklif formu hazırlanıyor...")
                excel_path = self.excel_handler.create_offer(customer_data, services, offer_info)
                subtotal = sum(s['quantity'] * s['unit_price'] for s in services)
                kdv = subtotal * config.KDV_RATE
                total = subtotal + kdv

                # Excel'i PDF'e çevir
                pdf_path = self.pdf_converter.excel_to_pdf(excel_path)
                if pdf_path and Path(pdf_path).exists():
                    pdf_files.append(pdf_path)

                # 2. Yetkilendirme Taahhütnamesi oluştur
                if tax_data and email:
                    await update.message.reply_text("📄 2/4 - Yetkilendirme Taahhütnamesi hazırlanıyor...")
                    word_file = self.document_handler.fill_yetkilendirme_taahhutnamesi(tax_data)
                    if word_file:
                        word_pdf = self.document_handler.convert_to_pdf(word_file)
                        if word_pdf and Path(word_pdf).exists():
                            pdf_files.append(word_pdf)

                    # 3. Kullanıcı Yetkilendirme Formu oluştur
                    await update.message.reply_text("📄 3/4 - Kullanıcı Yetkilendirme Formu hazırlanıyor...")
                    excel_form = self.document_handler.fill_kullanici_yetkilendirme_formu(tax_data, email)
                    if excel_form:
                        excel_form_pdf = self.document_handler.convert_to_pdf(excel_form)
                        if excel_form_pdf and Path(excel_form_pdf).exists():
                            pdf_files.append(excel_form_pdf)

            # Eğer kullanıcı Proje seçtiyse sözleşme ve KOSGEB Vekaletname oluştur
            elif context.user_data.get('initial_choice') == 'PROJE':
                proje_turu = context.user_data.get('proje_turu')
                ucret_bilgisi = context.user_data.get('ucret_bilgisi')
                if proje_turu and ucret_bilgisi and tax_data:
                    # 1. Sözleşme
                    await update.message.reply_text("📄 1/2 - Sözleşme hazırlanıyor...")
                    sozlesme_file = self.document_handler.fill_sozlesme(tax_data, proje_turu, ucret_bilgisi)
                    if sozlesme_file:
                        sozlesme_pdf = self.document_handler.convert_to_pdf(sozlesme_file)
                        if sozlesme_pdf and Path(sozlesme_pdf).exists():
                            pdf_files.append(sozlesme_pdf)
                    
                    # 2. KOSGEB Vekaletname
                    await update.message.reply_text("📄 2/2 - KOSGEB Vekaletname hazırlanıyor...")
                    # Email bilgisini tax_data'ya ekle
                    tax_data_with_email = tax_data.copy()
                    tax_data_with_email['email'] = email
                    
                    kosgeb_file = self.document_handler.fill_kosgeb_vekaletname(tax_data_with_email)
                    if kosgeb_file:
                        kosgeb_pdf = self.document_handler.convert_to_pdf(kosgeb_file)
                        if kosgeb_pdf and Path(kosgeb_pdf).exists():
                            pdf_files.append(kosgeb_pdf)
            
            # Hesaplamaları garanti altına al
            if context.user_data.get('initial_choice') == 'YTB':
                subtotal = sum(s['quantity'] * s['unit_price'] for s in services)
            else:
                subtotal = 0
            kdv = subtotal * config.KDV_RATE
            total = subtotal + kdv

            # Tüm PDF'leri gönder
            success_msg = config.MESSAGES['success'].format(subtotal=subtotal, kdv=kdv, total=total)
            
            if pdf_files:
                # PDF'leri context'e kaydet (email için)
                context.user_data['pdf_files'] = pdf_files
                context.user_data['customer_name'] = customer_data['name']
                
                await update.message.reply_text(f"✅ {len(pdf_files)} belge oluşturuldu!")
                for i, pdf_file in enumerate(pdf_files, 1):
                    with open(pdf_file, 'rb') as f:
                        caption = success_msg if i == 1 else None
                        await update.message.reply_document(
                            document=f,
                            filename=Path(pdf_file).name,
                            caption=caption,
                            parse_mode='Markdown' if caption else None
                        )
                
                # Email gönderme seçeneği sun
                if self.email_sender.enabled:
                    keyboard = [['✅ Evet, e-posta gönder', '❌ Hayır, gerek yok']]
                    await update.message.reply_text(
                        "📧 *Bu belgeleri e-posta ile göndermek ister misiniz?*",
                        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
                        parse_mode='Markdown'
                    )
                    return ASK_SEND_EMAIL
                else:
                    # Email devre dışıysa PDF'leri sil ve bitir
                    for pdf_file in pdf_files:
                        Path(pdf_file).unlink(missing_ok=True)
                    return ConversationHandler.END
            else:
                # PDF oluşturulamadıysa Excel gönder
                with open(excel_path, 'rb') as f:
                    await update.message.reply_document(
                        document=f, 
                        filename=Path(excel_path).name, 
                        caption=success_msg + "\n\n⚠️ PDF oluşturulamadı, Excel gönderildi.", 
                        parse_mode='Markdown'
                    )
                return ConversationHandler.END
        except Exception as e:
            logger.error(f'Hata: {e}')
            import traceback
            traceback.print_exc()
            await update.message.reply_text(f"❌ Hata: {e}")
            return ConversationHandler.END
    
    async def ask_send_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """E-posta gönderme kararını al"""
        choice = update.message.text.strip().lower()
        
        if 'evet' in choice or 'gönder' in choice:
            # E-posta adresini sor
            await update.message.reply_text(
                "📧 *Belgeleri göndermek istediğiniz e-posta adresini yazın:*\n\n"
                "Örnek: musteri@firma.com",
                reply_markup=ReplyKeyboardRemove(),
                parse_mode='Markdown'
            )
            return ASK_EMAIL_FOR_SENDING
        else:
            await update.message.reply_text(
                "👌 Tamam, e-posta gönderilmedi.",
                reply_markup=ReplyKeyboardRemove()
            )
            
            # PDF'leri temizle
            pdf_files = context.user_data.get('pdf_files', [])
            for pdf_file in pdf_files:
                Path(pdf_file).unlink(missing_ok=True)
            
            return ConversationHandler.END
    
    async def send_email_to_address(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Belgeleri girilen e-posta adresine gönder"""
        to_email = update.message.text.strip()
        
        # E-posta formatı kontrolü
        if '@' not in to_email or '.' not in to_email:
            await update.message.reply_text(
                "❌ Geçersiz e-posta adresi!\n\n"
                "Lütfen geçerli bir e-posta adresi girin (örn: musteri@firma.com):"
            )
            return ASK_EMAIL_FOR_SENDING
        
        await update.message.reply_text(
            f"📧 E-posta gönderiliyor: {to_email}...",
            reply_markup=ReplyKeyboardRemove()
        )
        
        pdf_files = context.user_data.get('pdf_files', [])
        customer_name = context.user_data.get('customer_name', 'Müşteri')
        contact_person = context.user_data.get('contact_person', '')
        
        # E-posta gönder
        success = self.email_sender.send_offer_email(
            to_email=to_email,
            customer_name=customer_name,
            pdf_files=pdf_files,
            contact_person=contact_person
        )
        
        if success:
            await update.message.reply_text(
                f"✅ *E-posta başarıyla gönderildi!*\n\n"
                f"📧 Alıcı: {to_email}\n"
                f"📎 {len(pdf_files)} belge eklendi",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ E-posta gönderilemedi!\n\n"
                "Belgeler Telegram'da size iletildi.",
                parse_mode='Markdown'
            )
        
        # PDF'leri temizle
        for pdf_file in pdf_files:
            Path(pdf_file).unlink(missing_ok=True)
        
        return ConversationHandler.END
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(config.MESSAGES['cancelled'], reply_markup=ReplyKeyboardRemove(), parse_mode='Markdown')
        return ConversationHandler.END

def main():
    if not config.TELEGRAM_BOT_TOKEN or config.TELEGRAM_BOT_TOKEN == 'your_bot_token_here':
        print("❌ Token tanımlı değil!")
        return
    
    bot = OfferBot()
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('yeni', bot.new_offer)],
        states={
            ASK_INITIAL_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_initial_choice)],
            ASK_TAX_PDF: [
                MessageHandler(filters.Document.PDF, bot.receive_tax_pdf),
                MessageHandler(filters.PHOTO, bot.receive_tax_photo)
            ],
            ASK_MANUAL_ENTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.ask_manual_entry_response)],
            ASK_MANUAL_COMPANY: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_manual_company)],
            ASK_MANUAL_TAX_OFFICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_manual_tax_office)],
            ASK_MANUAL_TAX_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_manual_tax_number)],
            ASK_MANUAL_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_manual_address)],
            ASK_TAX_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_tax_number)],
            ASK_CONTACT_PERSON: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_contact_person)],
            ASK_OFFER_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_offer_date_choice)],
            ASK_MANUAL_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_manual_date)],
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_email)],
            ASK_SERVICE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_service_name)],
            ASK_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_quantity)],
            ASK_UNIT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_unit_price)],
            ASK_ADD_MORE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.ask_add_more)],
            ASK_NOTES_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_notes_choice)],
            ASK_NOTES_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_notes_text)],
            ASK_DELIVERY_DATE_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_delivery_date_choice)],
            ASK_DELIVERY_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_delivery_date)],
            ASK_PROJECT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_project_type)],
            ASK_CONTRACT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_contract_amount)],
            ASK_SEND_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.ask_send_email)],
            ASK_EMAIL_FOR_SENDING: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.send_email_to_address)],
        },
        fallbacks=[CommandHandler('iptal', bot.cancel)],
    )
    
    application.add_handler(CommandHandler('start', bot.start))
    application.add_handler(conv_handler)
    
    print("🤖 Bot başlatılıyor...")
    print("📱 Bot: @arslanli_danismanlik_bot")
    print("✅ Çalışıyor! Durdurmak için Ctrl+C")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
