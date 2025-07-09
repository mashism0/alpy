import os
from dotenv import load_dotenv
import datetime
from database.models import Instructor
from aiogram import Router, F  # Маршрутизация и фильтры для бота Aiogram
from aiogram.types import CallbackQuery, Message  # Типы Telegram-сообщений
from aiogram.fsm.context import FSMContext  # Контекст состояний FSM
from aiogram.fsm.state import State, StatesGroup  # Определение состояний FSM
from aiogram.filters.state import StateFilter 
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

load_dotenv() #загрузка переменных из env

callback_router = Router()

class QRStates(StatesGroup):
    waiting_fio = State() 


DATABASE_URL = os.getenv("DATABASE_URL") #получение строки подключения к бд из окружения 
engine = create_async_engine(DATABASE_URL, echo=True) #создаем движок для подключения к БД
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False) #Создает асинхронный движок SQLAlchemy, который будет использовать драйвер asyncpg


@callback_router.callback_query(F.data == "check_fio")  # Обработчик нажатия на кнопку с data="check_qr"
async def process_check_fio(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Отправьте ФИО инструктора для проверки в формате:\n"
    "ФАМИЛИЯ ИМЯ ОТЧЕСТВО")  # Запросить фото у пользователя
    await state.set_state(QRStates.waiting_fio)  # Перевести FSM в состояние ожидания фото
    await callback.answer()  # Ответить на callback (чтобы убрать "часики" у кнопки)

@callback_router.message(StateFilter(QRStates.waiting_fio), F.text)  # Обработчик сообщений с фото в состоянии ожидания QR
async def handle_qr_photo(message: Message, state: FSMContext):
    fio = message.text.strip().split()
    if len(fio) != 3:
        await message.answer("❌ Пожалуйста, введите ФИО в формате: ФАМИЛИЯ ИМЯ ОТЧЕСТВО")
        return
    last_name = fio[0][:1].upper() + fio[0][1:].lower()
    print(last_name)
    first_name = fio[1][:1].upper() + fio[1][1:].lower()
    print(first_name)
    middle_name = fio[2][:1].upper() + fio[2][1:].lower()
    #или так     last_name, first_name, middle_name = map(str.capitalize, fio)
    
    AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession,) #Создает фабрику асинхронных сессий

    async with AsyncSessionLocal() as session: #сессия из фабрики сессий в ассинхронном контексте 
        user1 = await session.execute(select(Instructor).filter_by(last_name=last_name, first_name=first_name, middle_name=middle_name))#Выполняем асинхронный запрос к базе данных
        
    user = user1.scalar_one_or_none() #Получаем первую строку или None, если ничего не найдено

    if user:
        birth_date = user.birth_date.strftime('%d.%m.%Y') if user.birth_date else "Не указано"
        await message.answer(f"✅ Инструктор найден: {user.last_name} {user.first_name} {user.middle_name}\n"
                            f"Дата рождения: {birth_date}")
    else:
        await message.answer(f"❌ Инструктор не найден\n"
                             f"Проверьте правильность написания ФИО")
        print("❌ Пользователь с таким ФИО не найден")

    await state.clear()  # Сбрасываем состояние FSM





@callback_router.callback_query(F.data == 'exam')
async def process_check_qr(callback:CallbackQuery):
    await callback.message.answer('Введите ваш email для регистрации')
    await callback.anwer()
