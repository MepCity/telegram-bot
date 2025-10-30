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
    
    def send_offer_email(self, to_email, customer_name, pdf_files):
        """
        Teklif belgelerini e-posta ile gönder
        
        Args:
            to_email: Alıcı e-posta adresi
            customer_name: Müşteri adı
            pdf_files: PDF dosya yolları listesi
            
        Returns:
            bool: Başarılı ise True
        """
        if not self.enabled:
            logger.warning('❌ Email gönderimi devre dışı (SendGrid API Key eksik)')
            return False
        
        logger.info(f'📧 E-posta hazırlanıyor: {to_email}')
        
        try:
            # E-posta içeriği (HTML)
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2 style="color: #2c3e50;">Sayın {customer_name},</h2>
                    
                    <p>Talep etmiş olduğunuz teklif belgeleri ekte yer almaktadır.</p>
                    
                    <h3 style="color: #34495e;">Ek Belgeler:</h3>
                    <ul>
                        <li>✅ YTB Teklif Formu</li>
                        <li>✅ Yetkilendirme Taahhütnamesi</li>
                        <li>✅ Kullanıcı Yetkilendirme Formu</li>
                        <li>✅ Sözleşme</li>
                    </ul>
                    
                    <p>Belgelerle ilgili herhangi bir sorunuz olursa lütfen bizimle iletişime geçiniz.</p>
                    
                    <br>
                    <p style="color: #7f8c8d; font-size: 12px;">
                        Bu e-posta otomatik olarak oluşturulmuştur.<br>
                        <strong>ARSLANLI DANIŞMANLIK</strong><br>
                        Hatice Arslan
                    </p>
                </body>
            </html>
            """
            
            # E-posta mesajı oluştur
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=f'Teklif Belgeleriniz - {customer_name}',
                html_content=html_content
            )
            
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
