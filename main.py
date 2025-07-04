import os
import asyncio
from random import randint
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from yt_dlp import YoutubeDL
import re

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6296302270
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
user_video_urls = {}

# --- Foydalanuvchini users.txt ga yozish ---
def add_user_to_file(user_id, first_name):
    try:
        # Fayl yo'q bo'lsa yaratadi
        if not os.path.exists("users.txt"):
            with open("users.txt", "w", encoding="utf-8") as f:
                pass

        with open("users.txt", "r+", encoding="utf-8") as f:
            users = f.read().splitlines()
            if str(user_id) not in [u.split(":")[0] for u in users]:
                f.write(f"{user_id}:{first_name}\n")
                print(f"✅ User yozildi: {user_id} - {first_name}")
            else:
                print(f"ℹ️ User allaqachon bor: {user_id}")
    except Exception as e:
        print(f"❌ users.txt yozishda xatolik: {e}")

# --- Video yuklab olish ---
async def download_video_or_audio(url, format_type="video"):
    file_id = randint(1000, 9999)
    output_path = f"{file_id}.%(ext)s"
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'bestvideo+bestaudio/best' if format_type == "video" else 'bestaudio/best',
        'merge_output_format': 'mp4' if format_type == "video" else None,
        'quiet': True
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename, info

# --- /start komandasi ---
@dp.message(CommandStart())
async def start(message: types.Message):
    add_user_to_file(message.from_user.id, message.from_user.first_name)  # User yoziladi
    await message.answer("👋 Salom! Menga YouTube, Instagram yoki TikTok linkini yuboring.")

# --- /about komandasi ---
@dp.message(Command("about"))
async def about(message: types.Message):
    await message.answer(
        "ℹ️ <b>Bot haqida:</b>\n\n"
        "🎬 Video yuklash\n"
        "🎵 Audio yuklash\n"
        "📄 Sarlavhani chiqarish\n\n"
        "👨‍💻 Dasturchi: Salohiddin\n"
        "📬 Aloqa: @salikh_658",
        parse_mode="HTML"
    )

# --- /users komandasi (faqat admin uchun) ---
@dp.message(Command("users"))
async def users(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Sizda bu komandani ishlatish huquqi yo‘q.")
        return

    if not os.path.exists("users.txt"):
        await message.answer("👥 Hech qanday foydalanuvchi topilmadi.")
        return

    with open("users.txt", "r", encoding="utf-8") as f:
        users = f.read().splitlines()

    if not users:
        await message.answer("👥 Foydalanuvchilar ro‘yxati bo‘sh.")
        return

    response = f"👥 <b>Bot foydalanuvchilari:</b>\n\n"
    for idx, user in enumerate(users, start=1):
        user_id, first_name = user.split(":", 1)
        response += f"{idx}. <b>{first_name}</b> (ID: <code>{user_id}</code>)\n"

    response += f"\n<b>Jami:</b> {len(users)} ta foydalanuvchi"
    await message.answer(response, parse_mode="HTML")

# --- Faqat linklarga javob berish va foydalanuvchini yozib qo‘yish ---
@dp.message()
async def handle_link(message: types.Message):
    text = message.text or ""
    link_pattern = r"(https?://)?(www\.)?(youtube\.com|youtu\.be|instagram\.com|tiktok\.com)/[^\s]+"

    if not re.search(link_pattern, text):
        return

    add_user_to_file(message.from_user.id, message.from_user.first_name)  # User yoziladi

    url = text.strip()
    loading_msg = await message.answer("📥 Video haqida ma'lumot olinmoqda...")

    try:
        with YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)

        title = info.get('title')
        if not title or "video by" in title.lower():
            desc = info.get('description', '')
            if desc.strip():
                title = desc.strip().split('\n')[0]
            else:
                title = info.get('uploader', 'Noma’lum video')

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

# --- Inline tugmalarni boshqarish ---
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

# --- Botni ishga tushirish ---
async def main():
    print("✅ Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
