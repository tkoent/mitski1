import telebot
import pytesseract
from PIL import Image
import re
import io
from flask import Flask

# أدخل رمز الـ API الخاص بالبوت هنا
API_TOKEN = '7553178989:AAEKLPR96IXRgoj8tXhUINMDy6EzbSCTLAs'
bot = telebot.TeleBot(API_TOKEN)

# إعداد Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # تأكد من تثبيت Tesseract على نظامك

# قراءة الكلمات المحظورة من ملف no.txt
def load_banned_words():
    with open('no.txt', 'r', encoding='utf-8') as file:
        banned_words = [line.strip().lower() for line in file]
    return banned_words

banned_words = load_banned_words()

# دالة لإزالة التشكيل من النص
def remove_tashkeel(text):
    # إزالة جميع الحركات (التشكيلات) باستخدام التعبيرات المنتظمة
    return re.sub(r'[\u0617-\u061A\u064B-\u0652]', '', text)

# دالة لفحص ما إذا كانت الرسالة تحتوي على كلمات محظورة
def contains_banned_word(message_text):
    # تحويل النص إلى أحرف صغيرة لتجنب حساسية حالة الأحرف
    message_text = message_text.lower()
    
    # إزالة التشكيلات من النص
    message_text = remove_tashkeel(message_text)
    
    # البحث عن أي من الكلمات المحظورة في النص
    for word in banned_words:
        # إزالة التشكيلات من الكلمة المحظورة
        word = remove_tashkeel(word)
        
        # البحث باستخدام تعبيرات منتظمة لضمان مطابقة الكلمة سواءً كانت منفصلة أو ضمن جملة
        if re.search(r'\b' + re.escape(word) + r'\b', message_text):
            return True
    return False

# دالة لاستخراج النص من الصورة باستخدام Tesseract
def extract_text_from_image(image):
    text = pytesseract.image_to_string(image, lang='ara')  # اللغة العربية
    return text

# التعامل مع أي رسالة يتم إرسالها في المجموعة
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # التعامل مع النصوص
    if message.content_type == 'text':
        if contains_banned_word(message.text):
            try:
                # حذف الرسالة
                bot.delete_message(message.chat.id, message.message_id)
                print(f"Deleted message: {message.text}")
                
                # إرسال رسالة تنبيه للشخص مع منشن
                user_mention = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"
                warning_message = f"{user_mention}, هذه الكلمة محظورة، يرجى الالتزام بالقوانين."
                bot.send_message(message.chat.id, warning_message, parse_mode="Markdown")
                
            except Exception as e:
                print(f"Error: {e}")
    
    # التعامل مع الصور
    elif message.content_type == 'photo':
        # تحميل الصورة
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # فتح الصورة باستخدام PIL
        image = Image.open(io.BytesIO(downloaded_file))

        # استخراج النص من الصورة
        extracted_text = extract_text_from_image(image)
        
        if extracted_text:
            # إرسال النص المستخرج إلى المجموعة
            bot.reply_to(message, f"تم استخراج النص: {extracted_text}")
        else:
            bot.reply_to(message, "لم أتمكن من اكتشاف نص في هذه الصورة.")

# تشغيل البوت
def start_bot():
    bot.polling(none_stop=True)

# إعداد خادم Flask
app = Flask(__name__)

@app.route('/')
def home():
    return '<h1>الكلمات المحظورة</h1><ul>' + ''.join([f'<li>{word}</li>' for word in banned_words]) + '</ul>'

# تشغيل Flask وخادم البوت معًا
if __name__ == "__main__":
    import threading
    # تشغيل البوت في Thread منفصل
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.start()
    
    # تشغيل خادم Flask
    app.run(host="0.0.0.0", port=8080)
    