import logging
import os
import re
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile
from yt_dlp import YoutubeDL

from random import randint

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def on_start():
    print("bot started....")

async def download_video(url):
    ydl_opts = {
        'outtmpl': f'{randint(1, 1000)}.%(ext)s',
        'format': 'mp4',
        'noplaylist': True,
        'quiet': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer("👋 Salom! Menga YouTube, TikTok yoki Instagram linkini yuboring — men sizga videoni jo‘nataman.")

@dp.message(Command("about"))
async def about_handler(message: types.Message):
    await message.answer(
        "ℹ️ <b>Bot haqida</b>:\n"
        "Bu bot YouTube, TikTok va Instagram videolarini yuklab beradi.\n\n"
        "👨‍💻 Dasturchi: Axmadjonov Salohiddin"
        "📬 Bog‘lanish: @salikh_658",
        parse_mode="HTML"
    )

@dp.message(Command("help"))
async def help_handler(message: types.Message):
    await message.answer(
        "Salom! agar bot siz tashlagan havola (url) gadi videoni yuklab bermayotgan bolsa, video mualifi(aftori) videoni yuklab olishga ruxsat bermagan bolishi mumkin, yoki bot hatto ishlayotgandir yana urinib ko'ring"
    )

@dp.message()
async def handle_links(message: types.Message):
    text = message.text.strip()

    if re.match(r'https?://(www\.)?(youtube\.com|youtu\.be|tiktok\.com|instagram\.com)/[^\s]+', text):
        await message.answer("⏳ Yuklab olinmoqda...")

        try:
            filename = await download_video(text)
            video = FSInputFile(filename)
            await message.answer_video(video)
            os.remove(filename)
        except Exception as e:
            logging.error(f"Xatolik: {e}")
            await message.answer("❌ Video yuklab bo‘lmadi. Linkni tekshiring.")

async def main():
    dp.startup.register(on_start)
    await dp.start_polling(bot)

asyncio.run(main())