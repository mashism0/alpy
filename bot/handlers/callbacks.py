import os
from dotenv import load_dotenv
from bot.handlers.start import main_menu, back
from bot.handlers.func import send_temp_message, delete_temp_message
import re
from database.models import Instructor
from aiogram import Router, F  # Маршрутизация и фильтры для бота Aiogram
from aiogram.types import CallbackQuery, Message # Типы Telegram-сообщений 
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
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение: {e}")
    await callback.bot.send_message(chat_id=callback.from_user.id, text="Отправьте ФИО инструктора для проверки в формате:\n"
    "ФАМИЛИЯ ИМЯ ОТЧЕСТВО", reply_markup=back)  # Запросить фото у пользователя
    await state.set_state(QRStates.waiting_fio)  # Перевести FSM в состояние ожидания фото
    await callback.answer()  # Ответить на callback (чтобы убрать "часики" у кнопки)

@callback_router.message(StateFilter(QRStates.waiting_fio), F.text)
async def handle_qr_fio(message: Message, state: FSMContext):
    fio = message.text.strip().split()
    try:
        for part in fio:
            if not re.fullmatch(r"[А-Яа-яЁё\-]+", part):
                await message.answer("❌ ФИО может содержать только кириллицу и дефисы.")
                return
        if len(fio) == 2:
            last_name, first_name = map(str.capitalize, fio)

            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Instructor).filter_by(last_name=last_name, first_name=first_name)
                )
                users = result.scalars().all()

            if users:
                for user in users:
                    birth_date = user.birth_date.strftime('%d.%m.%Y') if user.birth_date else "Не указано"
                    await message.answer(
                        f"✅ Инструктор найден: {user.last_name} {user.first_name} {user.middle_name or ''}\n"
                        f"Дата рождения: {birth_date}"
                    )
                    await state.clear()
                    await main_menu(message)
            else:
                await message.answer("❌ Инструктор не найден\n" \
                "Проверьте правильность написания ФИО", reply_markup=back)
                print("❌ Пользователь с таким ФИО не найден")
                return

        elif len(fio) == 3:
            last_name, first_name, middle_name = map(str.capitalize, fio)

            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Instructor).filter_by(
                        last_name=last_name,
                        first_name=first_name,
                        middle_name=middle_name
                    )
                )
                users = result.scalars().all()
            if users:
                for user in users:
                    birth_date = user.birth_date.strftime('%d.%m.%Y') if user.birth_date else "Не указано"
                    await message.answer(
                        f"✅ Инструктор найден: {user.last_name} {user.first_name} {user.middle_name}\n"
                        f"Дата рождения: {birth_date}",
                        )
                    await main_menu(message)
                    await state.clear()
                    #await main_menu(message)
            else:
                await message.answer(
                    "❌ Инструктор не найден\n"
                    "Проверьте правильность написания ФИО",
                    reply_markup=back)
                print("❌ Пользователь с таким ФИО не найден")
                return
        else:
            await message.answer("❌ Пожалуйста, введите ФИО в формате: Фамилия Имя Отчество", reply_markup=back)
            return

    except Exception as e:
        print(f"Ошибка при парсинге: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, повторите попытку.", reply_markup=back)
        return

