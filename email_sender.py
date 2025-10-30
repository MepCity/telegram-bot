"""
E-posta Gönderim Modülü - SendGrid API
"""
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
from pathlib import Path
import os
import logging
import base64

logger = logging.getLogger(__name__)


class EmailSender:
    """SendGrid API ile e-posta gönder"""
    
    def __init__(self, sendgrid_api_key=None, from_email=None):
        """
        Args:
            sendgrid_api_key: SendGrid API Key
            from_email: Gönderen e-posta adresi
        """
        self.api_key = sendgrid_api_key or os.getenv('SENDGRID_API_KEY')
        self.from_email = from_email or os.getenv('SENDGRID_FROM_EMAIL') or 'hamasetyasir@gmail.com'
        
        # Debug: Environment variables'ı kontrol et
        logger.info(f'🔍 DEBUG - SENDGRID_API_KEY: {"*" * 20 if self.api_key else "None"}')
        logger.info(f'🔍 DEBUG - FROM_EMAIL: {self.from_email}')
        
        if not self.api_key:
            logger.warning('⚠️ SendGrid API Key eksik! SENDGRID_API_KEY environment variable\'ını ayarlayın.')
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f'✅ Email gönderimi aktif (SendGrid): {self.from_email}')
    
    def send_offer_email(self, to_email, customer_name, pdf_files, contact_person=None):
        """
        Teklif belgelerini e-posta ile gönder
        
        Args:
            to_email: Alıcı e-posta adresi
            customer_name: Müşteri adı
            pdf_files: PDF dosya yolları listesi
            contact_person: Yetkili kişi adı (opsiyonel)
            
        Returns:
            bool: Başarılı ise True
        """
        if not self.enabled:
            logger.warning('❌ Email gönderimi devre dışı (SendGrid API Key eksik)')
            return False
        
        logger.info(f'📧 E-posta hazırlanıyor: {to_email}')
        
        try:
            # Yetkili kişi ismini belirle
            greeting_name = contact_person if contact_person else customer_name
            
            # E-posta içeriği (HTML)
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                    <p style="margin-bottom: 15px;"><strong>Merhaba {greeting_name};</strong></p>
                    
                    <p style="margin-bottom: 15px;">Öncelikle yeni iş birliğimiz her iki firma için de hayırlı olmasını diler, daha nice güzel işlere vesile olmasını dilerim.</p>
                    
                    <p style="margin-bottom: 15px;">Teşvik belgesi için evraklar ekte, ekteki evraklardan sadece <strong>Taahhütname noterden</strong> çıkacak diğerlerini <strong>kaşe imza</strong> yapmanız yeterli bunların yanında <strong>PTT'den KEP adresi açtırmanız</strong> ve <strong>e-imza almanız</strong> gerekiyor. Notere giderken yanınıza <strong>kaşenizi ve imza sirküsünü</strong> almayı unutmayın.</p>
                    
                    <h3 style="color: #34495e; margin-top: 25px; margin-bottom: 10px;">📎 Ek Belgeler:</h3>
                    <ul style="margin-bottom: 20px;">
                        <li>✅ YTB Teklif Formu</li>
                        <li>✅ Yetkilendirme Taahhütnamesi (Noter)</li>
                        <li>✅ Kullanıcı Yetkilendirme Formu (Kaşe-İmza)</li>
                        <li>✅ Sözleşme (Kaşe-İmza)</li>
                    </ul>
                    
                    <p style="margin-bottom: 20px;">Her türlü soru ve bilgi için mail ile iletişime geçebilirsiniz.</p>
                    
                    <p style="margin-top: 30px; margin-bottom: 5px;"><strong>Saygılarımla;</strong></p>
                    <p style="color: #2c3e50; margin: 0;"><strong>Arslanlı Danışmanlık Ekibi</strong></p>
                </body>
            </html>
            """
            
            # E-posta mesajı oluştur
            from sendgrid.helpers.mail import Email, To
            
            message = Mail(
                from_email=Email(self.from_email, 'ARSLANLI DANIŞMANLIK - Hatice Arslan'),
                to_emails=To(to_email),
                subject='Yatırım Teşvik Belgeleri Hk.',
                html_content=html_content
            )
            
            # Reply-To ekle (cevaplarda bu adrese gitsin)
            message.reply_to = Email(self.from_email, 'ARSLANLI DANIŞMANLIK')
            
            # PDF dosyalarını ekle
            for pdf_path in pdf_files:
                if not Path(pdf_path).exists():
                    logger.warning(f'⚠️ Dosya bulunamadı: {pdf_path}')
                    continue
                
                with open(pdf_path, 'rb') as f:
                    file_data = f.read()
                    encoded_file = base64.b64encode(file_data).decode()
                    
                    attached_file = Attachment(
                        FileContent(encoded_file),
                        FileName(Path(pdf_path).name),
                        FileType('application/pdf'),
                        Disposition('attachment')
                    )
                    message.add_attachment(attached_file)
                    logger.info(f'� Eklendi: {Path(pdf_path).name}')
            
            # SendGrid ile gönder
            logger.info(f'📧 E-posta gönderiliyor (SendGrid): {to_email}')
            
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(message)
            
            logger.info(f'✅ E-posta başarıyla gönderildi! Status Code: {response.status_code}')
            return True
            
        except Exception as e:
            logger.error(f'❌ E-posta gönderme hatası: {e}')
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    # Test
    sender = EmailSender()
    
    if sender.enabled:
        test_files = ['outputs/test.pdf']  # Test için
        result = sender.send_offer_email(
            to_email='test@example.com',
            customer_name='Test Firma A.Ş.',
            pdf_files=test_files
        )
        print(f'Test sonucu: {result}')
    else:
        print('Gmail bilgileri ayarlanmamış. Test yapılamadı.')
