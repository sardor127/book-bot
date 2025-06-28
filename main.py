import logging
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from aiogram.contrib.middlewares.logging import LoggingMiddleware

API_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

user_data = {}
check_action = CallbackData("check", "action", "user_id")

lang_kb = ReplyKeyboardMarkup(resize_keyboard=True).add("🇷🇺 Русский", "🇺🇿 O‘zbekcha")

format_kb_ru = ReplyKeyboardMarkup(resize_keyboard=True).add("📄 PDF версия", "📦 Печатная версия", "🔙 Назад")
format_kb_uz = ReplyKeyboardMarkup(resize_keyboard=True).add("📄 PDF versiya", "📦 Bosma versiya", "🔙 Orqaga")

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer("Пожалуйста, выберите язык:\n\n🇷🇺 Русский\n🇺🇿 O‘zbek tili", reply_markup=lang_kb)

@dp.message_handler(lambda msg: msg.text in ["🇷🇺 Русский", "🇺🇿 O‘zbekcha"])
async def choose_lang(message: types.Message):
    lang = "ru" if "Русский" in message.text else "uz"
    user_data[message.from_user.id] = {"lang": lang}
    kb = format_kb_ru if lang == "ru" else format_kb_uz
    await message.answer("Выберите формат книги:" if lang == "ru" else "Kitob formatini tanlang:", reply_markup=kb)

@dp.message_handler(lambda msg: msg.text in ["📄 PDF версия", "📄 PDF versiya"])
async def choose_pdf(message: types.Message):
    lang = user_data[message.from_user.id]["lang"]
    user_data[message.from_user.id]["format"] = "pdf"
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 Назад" if lang == "ru" else "🔙 Orqaga")
    await message.answer(
        "🧾 Отправьте фото чека после оплаты на Click кошелёк: 8801 4072 3582 7287" if lang == "ru"
        else "🧾 Click to‘lov chek rasmini yuboring: 8801 4072 3582 7287",
        reply_markup=kb
    )

@dp.message_handler(lambda msg: msg.text in ["📦 Печатная версия", "📦 Bosma versiya"])
async def choose_print(message: types.Message):
    lang = user_data[message.from_user.id]["lang"]
    user_data[message.from_user.id]["format"] = "print"

    contact_btn = KeyboardButton(
        "📞 Отправить номер телефона" if lang == "ru" else "📞 Telefon raqamni yuborish", request_contact=True
    )
    location_btn = KeyboardButton(
        "📍 Отправить геолокацию" if lang == "ru" else "📍 Joylashuvni yuborish", request_location=True
    )
    back_btn = KeyboardButton(
        "🔙 Назад" if lang == "ru" else "🔙 Orqaga"
    )
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add(contact_btn).add(location_btn).add(back_btn)

    if lang == "ru":
        await message.answer(
            "📦 <b>Шаг 1:</b> Пожалуйста, отправьте ваш номер телефона и геолокацию для доставки.\n\n"
            "🏦 <b>Шаг 2:</b> Оплатите 100 000 сум на Click кошелёк:\n<b>8801 4072 3582 7287</b>\n\n"
            "📸 <b>Шаг 3:</b> Отправьте фото чека об оплате.",
            reply_markup=kb
        )
    else:
        await message.answer(
            "📦 <b>1-qadam:</b> Iltimos, telefon raqamingiz va joylashuvni yuboring.\n\n"
            "🏦 <b>2-qadam:</b> 100 000 so‘mni quyidagi Click raqamiga to‘lang:\n<b>8801 4072 3582 7287</b>\n\n"
            "📸 <b>3-qadam:</b> To‘lov chek rasmini yuboring.",
            reply_markup=kb
        )

@dp.message_handler(lambda msg: msg.text in ["🔙 Назад", "🔙 Orqaga"])
async def go_back(message: types.Message):
    lang = user_data.get(message.from_user.id, {}).get("lang")
    if lang:
        kb = format_kb_ru if lang == "ru" else format_kb_uz
        await message.answer("Выберите формат книги:" if lang == "ru" else "Kitob formatini tanlang:", reply_markup=kb)
    else:
        await message.answer("Пожалуйста, выберите язык:\n\n🇷🇺 Русский\n🇺🇿 O‘zbek tili", reply_markup=lang_kb)

@dp.message_handler(content_types=types.ContentType.CONTACT)
async def handle_contact(message: types.Message):
    user_data[message.from_user.id]["phone"] = message.contact.phone_number
    lang = user_data[message.from_user.id]["lang"]
    await message.answer("✅ Телефон получен." if lang == "ru" else "✅ Telefon qabul qilindi.")

@dp.message_handler(content_types=types.ContentType.LOCATION)
async def handle_location(message: types.Message):
    loc = message.location
    user_data[message.from_user.id]["location"] = f"https://www.google.com/maps?q={loc.latitude},{loc.longitude}"
    lang = user_data[message.from_user.id]["lang"]
    await message.answer("📍 Геолокация получена." if lang == "ru" else "📍 Joylashuv qabul qilindi.")
    await message.answer(
        "📸 Теперь отправьте фото чека об оплате (100 000 сум)." if lang == "ru"
        else "📸 Endi to‘lov chek rasmini yuboring (100 000 so‘m)."
    )

@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_photo(message: types.Message):
    uid = message.from_user.id
    lang = user_data[uid]["lang"]
    format_type = user_data[uid].get("format")

    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ Одобрить", callback_data=check_action.new(action="approve", user_id=uid)),
        InlineKeyboardButton("❌ Отказать", callback_data=check_action.new(action="deny", user_id=uid))
    )

    if format_type == "pdf":
        await bot.send_photo(OWNER_ID, message.photo[-1].file_id,
            caption=f"📩 Чек от @{message.from_user.username or 'Без username'} (ID: {uid})\nФормат: PDF",
            reply_markup=markup
        )
    elif format_type == "print":
        phone = user_data[uid].get("phone", "❓")
        loc = user_data[uid].get("location", "❓")
        await bot.send_photo(OWNER_ID, message.photo[-1].file_id,
            caption=f"📦 Заказ печатной книги\n👤 @{message.from_user.username or 'Без username'} (ID: {uid})\n📞 {phone}\n📍 {loc}",
            reply_markup=markup
        )

@dp.callback_query_handler(check_action.filter())
async def handle_decision(call: types.CallbackQuery, callback_data: dict):
    action = callback_data["action"]
    uid = int(callback_data["user_id"])
    lang = user_data.get(uid, {}).get("lang", "ru")

    if action == "deny":
        await bot.send_message(uid, "❌ К сожалению, ваш чек отклонён." if lang == "ru" else "❌ Afsuski, chekingiz rad etildi.")
        await call.answer("Отказано")
        return

    # ✅ Вот этот блок должен быть внутри handle_decision
    if user_data.get(uid, {}).get("format") == "pdf":
        file_path = "Секреты_успешного_предпринимательства_.pdf" if lang == "ru" else "Muvaffaqiyatli tadbirkorlikning sirlari.pdf"
        try:
            with open(file_path, "rb") as f:
                await bot.send_document(uid, f)
            msg = "💚 Спасибо за покупку. Все средства направляются на помощь детям с онкологией." if lang == "ru" \
                else "💚 Sotib olganingiz uchun rahmat. Barcha mablag‘lar bolalar onkologiyasi uchun xayriya qilinadi."
            await bot.send_message(uid, msg)
            await call.answer("Отправлено")
        except Exception as e:
            await call.answer("Ошибка при отправке", show_alert=True)
            await bot.send_message(OWNER_ID, f"❗ Ошибка отправки PDF: {e}")
    else:
        await bot.send_message(uid,
            "✅ Ваш заказ принят. Мы свяжемся с вами в ближайшее время.\n\n"
            "💚 Все средства направляются на помощь детям с онкологией." if lang == "ru"
            else
            "✅ Buyurtmangiz qabul qilindi. Tez orada siz bilan bog'lanamiz.\n\n"
            "💚 Barcha mablag‘lar bolalar onkologiyasi uchun xayriya qilinadi."
        )
        await call.answer("Принято")

@dp.message_handler(lambda msg: user_data.get(msg.from_user.id, {}).get("format") == "print")
async def warn_invalid_input_for_print(message: types.Message):
    lang = user_data[message.from_user.id]["lang"]
    await message.answer(
        "📌 Пожалуйста, используйте кнопки ниже для отправки номера и геолокации. Затем прикрепите фото чека." if lang == "ru"
        else "📌 Iltimos, quyidagi tugmalar orqali telefon va joylashuv yuboring. Keyin to‘lov chekini biriktiring."
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
