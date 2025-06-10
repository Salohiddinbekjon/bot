import logging
import os
import re
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile
from yt_dlp import YoutubeDL
from  dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

async def download_video(url):
    ydl_opts = {
        'outtmpl': 'video.%(ext)s',
        'format': 'mp4',
        'noplaylist': True,
        'quiet': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("👋 Salom! Menga YouTube, TikTok yoki Instagram havolasini yuboring — men sizga videoni yuboraman 🎬")

@dp.message(Command("about"))
async def about(message: types.Message):
    await message.answer(
        "ℹ️ <b>Bot haqida</b>:\n"
        "Bu bot YouTube, TikTok va Instagram platformalaridan video yuklab berishga mo‘ljallangan.\n\n"
        "👨‍💻 Dasturchi: Axmadjonov Salohiddin\n"
        "📬 Muammo bo‘lsa bog‘laning: @pragromist",
        parse_mode="HTML"
    )

@dp.message()
async def handle_links(message: types.Message):
    text = message.text.strip()

    if re.match(r'https?://(www\.)?(youtube\.com|youtu\.be|tiktok\.com|instagram\.com)/[^\s]+', text):
        await message.answer("⏳ Video yuklab olinmoqda...")

        try:
            filename = await download_video(text)
            video = FSInputFile(filename)
            await message.answer_video(video)
            os.remove(filename)
        except Exception as e:
            logging.error(e)
            await message.answer("❌ Xatolik yuz berdi. Linkni tekshirib ko‘ring.")
    else:
        pass

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
