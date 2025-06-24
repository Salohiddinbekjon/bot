import logging
import os
import re
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message
from yt_dlp import YoutubeDL
from random import randint

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def on_start():
    print("bot started....")




user_video_urls = {}


async def download_video_or_audio(url, format_type="video"):
    file_id = randint(1000, 9999)
    
    if format_type == "audio":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{file_id}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
        }
    else:
        ydl_opts = {
            'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            'merge_output_format': 'mp4',
            'outtmpl': f'{file_id}.%(ext)s',
            'quiet': True,
        }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if format_type == "audio":
            filename = os.path.splitext(filename)[0] + ".mp3"
        return filename

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("👋 Salom! Menga YouTube, TikTok yoki Instagram linkini yuboring — men sizga videoni jo‘nataman.")

@dp.message(Command("about"))
async def about_handler(message: Message):
    await message.answer(
        "ℹ️ <b>Bot haqida</b>:\n"
        "Bu bot YouTube, TikTok va Instagram videolarini yuklab beradi va uni Audio farmata ham yuklab olishingiz mumkin.\n\n"
        "👨‍💻 Dasturchi: Axmadjonov Salohiddin"
        "📬 Bog‘lanish: @salikh_658",
        parse_mode="HTML"
    )

@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "Salom! agar bot siz tashlagan havola (url) gadi videoni yuklab bermayotgan bolsa, video mualifi(aftori) videoni yuklab olishga ruxsat bermagan bolishi mumkin, yoki bot hatto ishlayotgandir yana urinib ko'ring"
    )

@dp.message()
async def handle_links(message: Message):
    text = message.text.strip()
    if re.match(r'https?://(www\.)?(youtube\.com|youtu\.be|tiktok\.com|instagram\.com)/[^\s]+', text):
        user_video_urls[message.from_user.id] = text

        buttons = [
            [InlineKeyboardButton(text="🎬 Video yuklash", callback_data="download_video")],
            [InlineKeyboardButton(text="🎵 Audio yuklash", callback_data="download_audio")]
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer("📥 Yuklab olish turini tanlang:", reply_markup=keyboard)

@dp.callback_query(F.data.in_(['download_video', 'download_audio']))
async def process_download(call: types.CallbackQuery):
    await call.answer()

    user_id = call.from_user.id
    url = user_video_urls.get(user_id)

    if not url:
        await call.message.answer("❗ Link topilmadi. Iltimos, avval video link yuboring.")
        return

    format_type = "video" if call.data == "download_video" else "audio"
    waiting = await call.message.answer("⏳ Yuklab olinmoqda...")

    try:
        filename = await download_video_or_audio(url, format_type)
        media = FSInputFile(filename)

        if format_type == "audio":
            await call.message.answer_audio(media)
        else:
            await call.message.answer_video(media)

        await waiting.delete()
        os.remove(filename)

    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await waiting.edit_text("❌ Yuklab olishda xatolik yuz berdi.")


async def main():
    dp.startup.register(on_start)
    await dp.start_polling(bot)

asyncio.run(main())