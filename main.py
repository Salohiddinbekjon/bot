import os
import asyncio
from random import randint
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from yt_dlp import YoutubeDL
import re

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 6296302270
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
user_video_urls = {}

USERS_FILE = "users.txt"

def save_user(user_id, first_name):
    user_entry = f"{user_id} | {first_name}"
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            f.write(user_entry + "\n")
    else:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = f.read().splitlines()
        if user_entry not in users:
            with open(USERS_FILE, "a", encoding="utf-8") as f:
                f.write(user_entry + "\n")

async def download_video_or_audio(url, format_type="video"):
    file_id = randint(1000, 9999)
    output_path = f"{file_id}.%(ext)s"
    ydl_opts = {
        'outtmpl': output_path,
        'cookies': 'cookies.txt',  # Instagram uchun cookie
        'quiet': True,
        'merge_output_format': 'mp4',
    }

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
    save_user(message.from_user.id, message.from_user.first_name)
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

@dp.message(Command("users"))
async def show_users(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Siz bu komandani ishlata olmaysiz.")
        return

    if not os.path.exists(USERS_FILE):
        await message.answer("👥 Hozircha hech qanday foydalanuvchi yo‘q.")
        return

    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = f.read().splitlines()

    response = "👥 Foydalanuvchilar ro‘yxati:\n\n"
    count = 0
    for i, user in enumerate(users, 1):
        if "|" in user:
            user_id, name = user.split("|", 1)
            response += f"{i}. {name.strip()} (ID: {user_id.strip()})\n"
            count += 1

    response += f"\n🔢 Umumiy: {count} ta foydalanuvchi."
    await message.answer(response)

@dp.message()
async def handle_link(message: types.Message):
    text = message.text or ""
    link_pattern = r"(https?://)?(www\.)?(youtube\.com|youtu\.be|instagram\.com|tiktok\.com)/[^\s]+"

    if not re.search(link_pattern, text):
        return

    url = text.strip()
    loading_msg = await message.answer("📥 Video haqida ma'lumot olinmoqda...")

    try:
        with YoutubeDL({'quiet': True, 'cookies': 'cookies.txt'}) as ydl:
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
