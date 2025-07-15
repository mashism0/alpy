import os
from dotenv import load_dotenv
from aiogram import Router, F  # Маршрутизация и фильтры для бота Aiogram
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext  # Контекст состояний FSM
from aiogram.fsm.state import State, StatesGroup  # Определение состояний FSM
from aiogram.filters.state import StateFilter 
from pydantic import BaseModel, EmailStr


email_router = Router()

class QRStates(StatesGroup):
    waiting_email = State() 

class User(BaseModel):
    email: EmailStr






@email_router.callback_query(F.data == 'exam')
async def process_check_email(callback:CallbackQuery, state: FSMContext):
    await callback.message.answer('Введите ваш email для регистрации')
    await state.set_state(QRStates.waiting_email)
    await callback.answer()

@email_router.message(StateFilter(QRStates.waiting_email), F.text)
async def check_email(message: Message, state: FSMContext):
    try:
        user_data = {"email": message.text.strip()}
        user = User(**user_data)
        print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!Email валиден: {user.email}")
        await message.answer(f"Email успешно принят: {user.email}")
        await state.clear()

    except Exception as e:
        await message.answer(f"Некорректный email. Попробуйте ещё раз.")
        print(f"Ошибка валидации: {{'email': '{message.text.strip()}'}} | {e}")
