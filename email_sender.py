"""
E-posta Gönderim Modülü - Gmail SMTP
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)


class EmailSender:
    """Gmail SMTP ile e-posta gönder"""
    
    def __init__(self, gmail_user=None, gmail_password=None):
        """
        Args:
            gmail_user: Gmail adresi (ör: example@gmail.com)
            gmail_password: Gmail App Password (16 haneli)
        """
        self.gmail_user = gmail_user or os.getenv('GMAIL_USER')
        self.gmail_password = gmail_password or os.getenv('GMAIL_APP_PASSWORD')
        
        # Debug: Environment variables'ı kontrol et
        logger.info(f'🔍 DEBUG - GMAIL_USER: {self.gmail_user}')
        logger.info(f'🔍 DEBUG - GMAIL_APP_PASSWORD: {"*" * len(self.gmail_password) if self.gmail_password else "None"}')
        
        if not self.gmail_user or not self.gmail_password:
            logger.warning('⚠️ Gmail bilgileri eksik! GMAIL_USER ve GMAIL_APP_PASSWORD environment variable\'larını ayarlayın.')
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f'✅ Email gönderimi aktif: {self.gmail_user}')
    
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
            print('❌ Email gönderimi devre dışı (Gmail bilgileri eksik)')
            return False
        
        try:
            # E-posta mesajı oluştur
            msg = MIMEMultipart()
            msg['From'] = self.gmail_user
            msg['To'] = to_email
            msg['Subject'] = f'Teklif Belgeleriniz - {customer_name}'
            
            # E-posta içeriği (HTML)
            body = f"""
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
            
            msg.attach(MIMEText(body, 'html'))
            
            # PDF dosyalarını ekle
            for pdf_path in pdf_files:
                if not Path(pdf_path).exists():
                    logger.warning(f'⚠️ Dosya bulunamadı: {pdf_path}')
                    continue
                
                with open(pdf_path, 'rb') as f:
                    pdf_attachment = MIMEApplication(f.read(), _subtype='pdf')
                    pdf_attachment.add_header('Content-Disposition', 'attachment', 
                                            filename=Path(pdf_path).name)
                    msg.attach(pdf_attachment)
                    logger.info(f'📎 Eklendi: {Path(pdf_path).name}')
            
            # Gmail SMTP ile gönder
            logger.info(f'📧 E-posta gönderiliyor: {to_email}')
            
            # Port 587 (TLS) yerine Port 465 (SSL) dene
            import ssl
            context = ssl.create_default_context()
            
            try:
                # Önce Port 465 (SSL) ile dene
                logger.info('📡 Port 465 (SSL) ile bağlanılıyor...')
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context)
                server.login(self.gmail_user, self.gmail_password)
            except Exception as e:
                # Port 465 başarısız olursa Port 587 (TLS) dene
                logger.warning(f'⚠️ Port 465 başarısız: {e}')
                logger.info('📡 Port 587 (TLS) ile bağlanılıyor...')
                server = smtplib.SMTP('smtp.gmail.com', 587, timeout=30)
                server.starttls(context=context)
                server.login(self.gmail_user, self.gmail_password)
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f'✅ E-posta başarıyla gönderildi: {to_email}')
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
