import telebot
import yt_dlp
import os

# Bot tokeningiz
TOKEN = "7466043263:AAEn6vrNVC30OG5l5eACpJrOkXKCaLz15uI"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# Linkni aniqlovchi oddiy funksiya
def is_valid_url(text):
    return any(domain in text for domain in ["youtube.com", "youtu.be", "tiktok.com", "instagram.com"])

# Video yuklab olish funksiyasi
def download_video(url):
    try:
        ydl_opts = {
            'outtmpl': 'video.%(ext)s',
            'format': 'mp4',
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        print(f"Download error: {e}")
        return None

# Start buyrug'i
@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.reply_to(message, "👋 Salom! Instagram, YouTube yoki TikTok link yuboring — men videoni yuklab beraman!")

# Har qanday matn uchun handler
@bot.message_handler(func=lambda message: True, content_types=['text'])
def video_handler(message):
    url = message.text.strip()

    if is_valid_url(url):
        msg = bot.reply_to(message, "📥 Yuklanmoqda... Iltimos kuting.")
        filepath = download_video(url)
        if filepath and os.path.exists(filepath):
            try:
                with open(filepath, 'rb') as video:
                    bot.send_video(message.chat.id, video)
            except Exception as e:
                bot.reply_to(message, f"⚠️ Yuklab bo‘lmadi: {e}")
            finally:
                os.remove(filepath)
        else:
            bot.reply_to(message, "❌ Video yuklab bo‘lmadi. Linkni tekshiring.")
    else:
        bot.reply_to(message, "❗ Iltimos faqat Instagram, TikTok yoki YouTube link yuboring.")

# Botni ishga tushirish
if __name__ == 'main':
    print("Bot ishga tushdi...")
    bot.infinity_polling()