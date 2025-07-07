from aiogram import Router
from aiogram import F
from aiogram.types import CallbackQuery

callback_router = Router()


@callback_router.callback_query(F.data == 'check_fio')
async def process_check_qr(callback:CallbackQuery):
    await callback.message.answer('Отправьте ФИО инструктора для проверки.')
    await callback.anwer()

@callback_router.callback_query(F.data == 'exam')
async def process_check_qr(callback:CallbackQuery):
    await callback.message.answer('Введите ваш email для регистрации')
    await callback.anwer()
