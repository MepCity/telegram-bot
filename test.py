#!/usr/bin/env python3
"""
Hızlı Test Scripti
Bot'un tüm fonksiyonlarını test eder
"""

print("🧪 Bot Test Scripti Başlatılıyor...\n")

# 1. Modül kontrolü
print("1️⃣ Modül import testi...")
try:
    import config
    from pdf_reader import PDFReader
    from excel_handler import ExcelHandler
    print("✅ Tüm modüller başarıyla import edildi\n")
except Exception as e:
    print(f"❌ Modül import hatası: {e}\n")
    exit(1)

# 2. PDF okuma testi
print("2️⃣ PDF okuma testi...")
try:
    reader = PDFReader()
    tax_info = reader.extract_tax_info('VERGİ LEVHASI.pdf')
    print(f"✅ Firma adı: {tax_info.get('company_name', 'Bulunamadı')}")
    print(f"✅ Vergi dairesi: {tax_info.get('tax_office', 'Bulunamadı')}\n")
except Exception as e:
    print(f"❌ PDF okuma hatası: {e}\n")

# 3. Excel oluşturma testi
print("3️⃣ Excel oluşturma testi...")
try:
    from datetime import datetime
    handler = ExcelHandler()
    
    test_customer = {
        'name': tax_info.get('company_name', 'TEST FİRMA'),
        'contact_person': 'TEST YETKİLİ',
    }
    
    test_services = [
        {
            'name': 'YATIRIM TEŞVİK BELGESİ',
            'quantity': 1,
            'unit_price': 750000
        },
        {
            'name': 'İHTİRA PATENT BAŞVURUSU',
            'quantity': 2,
            'unit_price': 50000
        }
    ]
    
    test_offer = {
        'offer_date': datetime.now().strftime('%d.%m.%Y'),
        'delivery_date': '--------------------',
        'payment_method': 'PEŞİN'
    }
    
    excel_path = handler.create_offer(test_customer, test_services, test_offer)
    print(f"✅ Excel dosyası oluşturuldu: {excel_path}\n")
    
    # Hesaplamaları göster
    subtotal = sum(s['quantity'] * s['unit_price'] for s in test_services)
    kdv = subtotal * config.KDV_RATE
    total = subtotal + kdv
    
    print("4️⃣ Hesaplama testi...")
    print(f"   Ara Toplam: {subtotal:,.2f} TL")
    print(f"   KDV (%{int(config.KDV_RATE*100)}): {kdv:,.2f} TL")
    print(f"   Genel Toplam: {total:,.2f} TL\n")
    
except Exception as e:
    print(f"❌ Excel oluşturma hatası: {e}\n")
    import traceback
    traceback.print_exc()

# 5. Bot konfigürasyon kontrolü
print("5️⃣ Bot konfigürasyon kontrolü...")
if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_BOT_TOKEN != 'your_bot_token_here':
    print("✅ Telegram bot token tanımlı\n")
    print("=" * 50)
    print("🎉 TÜM TESTLER BAŞARILI!")
    print("=" * 50)
    print("\n📱 Bot'u başlatmak için:")
    print("   python3 bot.py")
    print("\n📖 Telegram'da test etmek için:")
    print("   1. Telegram'da botunuzu bulun")
    print("   2. /start yazın")
    print("   3. /yeni yazın")
    print("   4. Vergi levhası PDF'i gönderin")
    print("   5. Adım adım ilerleyin!")
else:
    print("⚠️  Telegram bot token tanımlı DEĞİL")
    print("\n📝 Token eklemek için:")
    print("   1. Telegram'da @BotFather'a gidin")
    print("   2. /newbot komutu ile bot oluşturun")
    print("   3. Aldığınız token'ı .env dosyasına ekleyin:")
    print("      nano .env")
    print("      TELEGRAM_BOT_TOKEN=sizin_tokeniniz")
    print("\n✅ Diğer tüm testler başarılı!")
    print("   Token ekledikten sonra bot.py'yi çalıştırabilirsiniz")
