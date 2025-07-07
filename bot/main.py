from aiogram import Bot, Dispatcher #Bot - для общения с тг, Dispatcher - для обработки сообщений, команд и тп.
import asyncio #для запуска асинхронной функции main().
import logging #чтобы видеть, что происходит в консоли.
import os #чтобы брать переменные окружения (например, токен бота).
from dotenv import load_dotenv
load_dotenv()

from handlers.qr_handler import qr_router #Обработка qr
from handlers.start import start_router #Команда /start
from handlers.callbacks import callback_router


TOKEN = os.getenv("BOT_TOKEN") #получаем токен из переменной окружения

async def main():
    bot = Bot(token=TOKEN) #объект бота
    dp = Dispatcher() #обработчик

    dp.include_router(start_router) #подключаем обработчик /start
    dp.include_router(qr_router) #подключаем обработчик qr
    dp.include_router(callback_router) #подключаем роутер в колбеки

    await dp.start_polling(bot) #запуск долгоживущего цикла, бот опрашивает Tg на предмет новых событий

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
    #Это нужно, чтобы main() запускалась только если файл запущен напрямую, а не импортирован.
