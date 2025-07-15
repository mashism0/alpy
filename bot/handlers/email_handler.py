import random
import string
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
from aiogram import Router, F  # Маршрутизация и фильтры для бота Aiogram
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext  # Контекст состояний FSM
from aiogram.fsm.state import State, StatesGroup  # Определение состояний FSM
from aiogram.filters.state import StateFilter 
from pydantic import BaseModel, EmailStr, ValidationError
import smtplib
from email.mime.text import MIMEText
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker 
from database.models import Instructor


load_dotenv() 

EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

email_router = Router()

email_and_code = {}

class EmailStates(StatesGroup):
    waiting_email = State() 
    waiting_code = State()

class User(BaseModel):
    email: EmailStr

DATABASE_URL = os.getenv("DATABASE_URL") #получение строки подключения к бд из окружения 
engine = create_async_engine(DATABASE_URL, echo=True) #создаем движок для подключения к БД
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False) #Создает асинхронный движок SQLAlchemy, который будет использовать драйвер asyncpg


@email_router.callback_query(F.data == 'exam')
async def process_check_email(callback:CallbackQuery, state: FSMContext):
    await callback.message.answer('Введите ваш email для аутентификации.\n'
                                  'Тот, который вы указывали в анкете.')
    await state.set_state(EmailStates.waiting_email)
    await callback.answer()

@email_router.message(StateFilter(EmailStates.waiting_email), F.text)
async def check_email(message: Message, state: FSMContext):
    try:
        user_data = {"email": message.text.strip()}
        user = User(**user_data)
        print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!Email валиден: {user.email}")
        
        AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession,) #Создает фабрику асинхронных сессий

        async with AsyncSessionLocal() as session: #сессия из фабрики сессий в ассинхронном контексте 
            user1 = await session.execute(select(Instructor).filter_by(email=user.email))#Выполняем асинхронный запрос к базе данных
            
        user = user1.scalar_one_or_none() #Получаем первую строку или None, если ничего не найдено

        if user:
            await message.answer(f"Email принят: {user.email}")
            code = ''.join(random.choices(string.digits, k=6))# Генерируем код из 6 символов
            email_and_code[user.email] = code  # Сохраняем код в словарь

            # Формируем письмо
            msg = MIMEText(f'Ваш код для входа: {code}')
            msg['Subject'] = 'Код аутентификации'
            msg['From'] = EMAIL_USERNAME
            msg['To'] = user.email

            # Отправляем письмо через SMTP (Email)
            try:
                with smtplib.SMTP_SSL('smtp.mail.ru', 465) as server:
                    print(f"{EMAIL_USERNAME}\n"
                        f"{EMAIL_PASSWORD}")
                    server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
                    server.send_message(msg)

                # Переход к следующему состоянию FSM
                await message.answer(f"✅ Код отправлен на {user.email}. Введите его в чат.")
                await state.set_state(EmailStates.waiting_code)

                # Сохраняем email в FSM для дальнейшей проверки
                await state.update_data(email=user.email)

            except Exception as e:
                await message.answer(f"⚠️ Ошибка при отправке письма, попробуйте позже.")
                print(f"Ошибка: {e}")
                email_and_code.pop(user.email, None)
                await state.clear()
        else:
            await message.answer(f"❌ Инструктор не найден\n"
                                f"Проверьте правильность написания email")
            print("❌ Пользователь с таким ФИО не найден")
            return

        
    except Exception as e:
        await message.answer(f"Некорректный email. Попробуйте ещё раз.")
        print(f"Ошибка валидации: {{'email': '{message.text.strip()}'}} | {e}")


# Обработка кода, введенного пользователем
@email_router.message(EmailStates.waiting_code, F.text)
async def process_code(message: Message, state: FSMContext):
    user_data = await state.get_data()
    email = user_data.get("email")
    code_input = message.text.strip()

    # Проверяем код
    if email_and_code.get(email) == code_input:
        await message.answer("🎉 Аутентификация успешна!")
        email_and_code.pop(email, None)  # Удаляем использованный код
        await state.clear()
    else:
        await message.answer("❌ Неверный код. Попробуйте снова.")