from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton  # любое сообщение тг (фото, текст и тп)
from aiogram.filters import CommandStart #Фильтр для команды /start, используется в роутерах.
from aiogram import F #фильтры нового типа (F.photo фильтрует сообщения с фото)

start_router = Router()

@start_router.message(CommandStart())
async def start_handler(message:Message):
    welcome_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Проверить инструктора по QR", callback_data='check_qr'),
                ],
            [
                InlineKeyboardButton(text='Проверить инструктора по ФИО', callback_data='check_fio'),
                ],
            [
                InlineKeyboardButton(text='Записаться на экзамен', callback_data='exam')
            ]
        ]
    )
    await message.reply(
        'Привет!\n'
        'Чем могу помочь?', reply_markup=welcome_keyboard)



