from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery  # любое сообщение тг (фото, текст и тп)
from aiogram.filters import CommandStart #Фильтр для команды /start, используется в роутерах.
from aiogram import F #фильтры нового типа (F.photo фильтрует сообщения с фото)

start_router = Router()

@start_router.message(CommandStart())
async def start_handler(message: Message):
    await message.reply(
        'Привет!\n'
        'Чем могу помочь?'
        )
    await main_menu(message)

async def main_menu(message:Message):
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
    await message.answer(
        "Что умеет этот бот:\n",
        reply_markup=welcome_keyboard
    )

back = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Вернуться в меню", callback_data='back_to_menu')]
    ]
)

@start_router.callback_query(F.data == "back_to_menu")
async def handle_back_to_menu(callback: CallbackQuery):
    await callback.message.delete()  # Удаляем сообщение с кнопкой "вернуться"
    await main_menu(callback.message)
    await callback.answer()


