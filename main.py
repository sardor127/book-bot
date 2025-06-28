import logging
from aiogram import Bot, Dispatcher, types, executor
from dotenv import load_dotenv
import os

load_dotenv()

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    await message.reply("✋ Отправьте скриншот чека для получения книги.")

@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_photo(message: types.Message):
    if message.from_user.id == OWNER_ID:
        return  # владелец не должен обрабатывать свои фото

    # Пересылаем фото владельцу
    await bot.send_photo(
        OWNER_ID,
        photo=message.photo[-1].file_id,
        caption=f"Получен чек от @{message.from_user.username or 'без ника'} ({message.from_user.id})",
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("📘 PDF на русском", callback_data=f"pdf_ru:{message.from_user.id}"),
            types.InlineKeyboardButton("📗 PDF на узбекском", callback_data=f"pdf_uz:{message.from_user.id}"),
            types.InlineKeyboardButton("❌ Отказать", callback_data=f"reject:{message.from_user.id}")
        )
    )

@dp.callback_query_handler(lambda c: c.data)
async def process_callback(callback_query: types.CallbackQuery):
    action, user_id = callback_query.data.split(":")
    user_id = int(user_id)

    if callback_query.from_user.id != OWNER_ID:
        await callback_query.answer("Недостаточно прав.", show_alert=True)
        return

    if action == "pdf_ru":
        await bot.send_document(user_id, types.InputFile("book_ru.pdf"))
        await callback_query.answer("Отправлено PDF на русском.")
    elif action == "pdf_uz":
        await bot.send_document(user_id, types.InputFile("book_uz.pdf"))
        await callback_query.answer("Отправлено PDF на узбекском.")
    elif action == "reject":
        await bot.send_message(user_id, "⛔️ Ваш чек был отклонён.")
        await callback_query.answer("Отказ отправлен.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
