import os
import asyncio
from random import randint
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from yt_dlp import YoutubeDL
import re

BOT_TOKEN =os.getenv("BOT_TOKEN")
ADMIN_ID = 6296302270
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
user_video_urls = {}

# 🔥 Cookie faylini URL ga qarab tanlash funksiyasi
def get_cookie_file(url):
    if "youtube.com" in url or "youtu.be" in url:
        return "youtubeCookies.txt"
    elif "instagram.com" in url:
        return "cookies.txt"
    else:
        return None  # Boshqa saytlar uchun cookie kerak emas

async def download_video_or_audio(url, format_type="video"):
    file_id = randint(1000, 9999)
    output_path = f"{file_id}.%(ext)s"

    # Cookie faylni tanlash
    cookie_file = get_cookie_file(url)

    ydl_opts = {
        'outtmpl': output_path,
        'quiet': True,
        'merge_output_format': 'mp4',
    }

    # Agar cookie kerak bo‘lsa, qo‘shamiz
    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file

    if format_type == "video":
        ydl_opts.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            }],
        })
    else:
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if format_type == "audio":
            filename = os.path.splitext(filename)[0] + ".mp3"
        return filename, info

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("👋 Salom! Menga YouTube, Instagram yoki TikTok linkini yuboring, men sizga video, audio va sarlavhasini chiqarib beraman.")

@dp.message(Command("about"))
async def about(message: types.Message):
    await message.answer(
        "ℹ️ Bot haqida:\n\n"
        "🎬 Video yuklash\n"
        "🎵 Audio yuklash\n"
        "📄 Sarlavhani chiqarish\n\n"
        "👨‍💻 Dasturchi: Salohiddin\n"
        "📬 Aloqa: @salikh_658"
    )

@dp.message()
async def handle_link(message: types.Message):
    text = message.text or ""
    link_pattern = r"(https?://)?(www\.)?(youtube\.com|youtu\.be|instagram\.com|tiktok\.com)/[^\s]+"

    if not re.search(link_pattern, text):
        return

    url = text.strip()
    loading_msg = await message.answer("📥 Video haqida ma'lumot olinmoqda...")

    try:
        # Cookie faylni tanlash
        cookie_file = get_cookie_file(url)
        ydl_opts = {'quiet': True}

        if cookie_file:
            ydl_opts['cookiefile'] = cookie_file

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        title = info.get('title')
        if not title or "video by" in title.lower():
            desc = info.get('description', 'Noma’lum video')
            title = desc.strip().split('\n')[0]

        thumb = info.get('thumbnail', None)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎬 Video yuklash", callback_data="video")],
            [InlineKeyboardButton(text="🎵 Audio yuklash", callback_data="audio")],
            [InlineKeyboardButton(text="📄 Sarlavhani chiqarish", callback_data="title")],
        ])

        if thumb:
            sent = await message.answer_photo(photo=thumb, caption=f"🎬 {title}", reply_markup=keyboard)
        else:
            sent = await message.answer(f"🎬 {title}", reply_markup=keyboard)

        await loading_msg.delete()

        user_video_urls[message.from_user.id] = {
            "url": url,
            "title": title,
            "thumb_msg_id": sent.message_id
        }

    except Exception as e:
        await loading_msg.delete()
        await message.answer(f"❌ Xatolik: {e}")

@dp.callback_query()
async def handle_callback(call: CallbackQuery):
    user_id = call.from_user.id
    data = user_video_urls.get(user_id)
    if not data:
        await call.answer("❗ Avval video link yuboring.")
        return

    url = data["url"]
    title = data["title"]
    thumb_msg_id = data["thumb_msg_id"]

    if call.data == "video":
        await call.answer("📥 Video yuklab olinmoqda...")
        filename, _ = await download_video_or_audio(url, "video")
        await call.message.answer_video(FSInputFile(filename), caption=f"🎬 {title}")
        os.remove(filename)

    elif call.data == "audio":
        await call.answer("📥 Audio yuklab olinmoqda...")
        filename, _ = await download_video_or_audio(url, "audio")
        await call.message.answer_audio(FSInputFile(filename), caption=f"🎵 {title}")
        os.remove(filename)

    elif call.data == "title":
        await call.answer("📄 Sarlavha chiqarilmoqda...")
        await call.message.answer(f"🎬 Video nomi:\n{title}")

    try:
        await bot.delete_message(call.message.chat.id, thumb_msg_id)
    except:
        pass

async def main():
    print("✅ Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
