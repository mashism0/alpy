import os  # Работа с файлами и операционной системой
from bot.handlers.start import main_menu, back
from bot.handlers.func import send_temp_message, delete_temp_message
import tempfile  # Создание временных файлов
import asyncio  # Асинхронное программирование
from concurrent.futures import ThreadPoolExecutor  # Запуск блокирующего кода в пуле потоков

import cv2  # OpenCV для работы с изображениями и QR-кодами
from selenium import webdriver  # Управление браузером через Selenium
from selenium.webdriver.chrome.service import Service  # Управление службой chromedriver
from selenium.webdriver.chrome.options import Options  # Опции для Chrome
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By  # Поиск элементов на странице
from selenium.webdriver.support.ui import WebDriverWait  # Ожидание элементов
from selenium.webdriver.support import expected_conditions as EC  # Условия для ожидания

from aiogram import Router, F  # Маршрутизация и фильтры для бота Aiogram
from aiogram.types import CallbackQuery, Message  # Типы Telegram-сообщений
from aiogram.fsm.context import FSMContext  # Контекст состояний FSM
from aiogram.fsm.state import State, StatesGroup  # Определение состояний FSM
from aiogram.filters.state import StateFilter  # Фильтр по состоянию


qr_router = Router()  # Создаём роутер для обработки команд, связанных с QR

class QRStates(StatesGroup):
    waiting_for_qr_photo = State()  # Определяем состояние ожидания фото с QR-кодом

@qr_router.callback_query(F.data == "check_qr")  # Обработчик нажатия на кнопку с data="check_qr"
async def ask_for_qr_photo(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение: {e}")
    await callback.message.answer("📸 Пожалуйста, отправьте фото QR-кода с удостоверения инструктора.",
                                  reply_markup=back)  # Запросить фото у пользователя
    await state.set_state(QRStates.waiting_for_qr_photo)  # Перевести FSM в состояние ожидания фото
    await callback.answer()  # Ответить на callback (чтобы убрать "часики" у кнопки)

@qr_router.message(StateFilter(QRStates.waiting_for_qr_photo), F.photo)  # Обработчик сообщений с фото в состоянии ожидания QR
async def handle_qr_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]  # Берём самое качественное фото (последний элемент списка)
    file_info = await message.bot.get_file(photo.file_id)  # Получаем информацию о файле

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:  # Создаём временный файл для фото
        file_path = tmp_file.name  # Запоминаем путь к временному файлу
        await message.bot.download_file(file_info.file_path, destination=file_path)  # Скачиваем фото в файл

    try:
        image = cv2.imread(file_path)  # Считываем фото через OpenCV
        if image is None:
            await message.answer("❌ Не удалось загрузить изображение.",
                                 reply_markup=back)  # Если не получилось прочитать - сообщаем об ошибке
            return

        detector = cv2.QRCodeDetector()  # Создаём детектор QR-кодов
        qr_data, _, _ = detector.detectAndDecode(image)  # Детектируем и декодируем QR-код
        if not qr_data:
            await message.answer("❌ Не удалось распознать QR-код. Пожалуйста, попробуйте снова и отправьте другое фото.",
                                 reply_markup=back)  # Если QR-код не распознан - сообщаем
            return

        if not qr_data.startswith("http"):  # Проверяем, что QR содержит ссылку
            await message.answer("❌ QR-код не содержит ссылку. Отправьте другой.",
                                 reply_markup=back)
            return
        
        if not qr_data.startswith("https://knd.gov.ru/"):  # Проверяем, что QR содержит ссылку
            await message.answer("❌ Отправлен неправильный QR-код. Отправьте корректный.",
                                 reply_markup=back)
            return
        await send_temp_message(message.bot, message, "🔍 Ищу информацию на сайте...")  # Информируем пользователя о начале парсинга

        info = await fetch_info_selenium(qr_data)  # Асинхронно вызываем функцию парсинга через Selenium

        await delete_temp_message(message.bot, message)
       
        if info:
            routes_text = "\n".join(info["route"][1:])
            hikes_text = "\n".join(info["hike"][1:])
            await message.answer(
                f"✅ Инструктор найден:\n"
                f"👤 ФИО: {info['full_name']}\n"
                f"📄 Статус удостоверения: {info['status']}\n"
                f"📍 Город проживания: {info['city']}\n"
                f"📋 Завершенные туристские маршруты:\n"
                f"{routes_text}\n"
                f"📋 Завершенные походы:\n"
                f"{hikes_text}"
            )  # Выводим результаты пользователю
            await state.clear()
            await main_menu(message)
        else:
            await message.answer("❌ Не удалось получить данные с сайта.")  # Ошибка при парсинге сайта
            await main_menu(message)
    finally:
        os.remove(file_path)  # Удаляем временный файл с фото
        #await state.clear()  # Сбрасываем состояние FSM

def fetch_info_selenium_sync(url: str) -> dict | None:
    options = Options()  # Создаём настройки для браузера
    options.headless = True  # Запуск в фоновом режиме без GUI
    #options.add_argument("--headless") #Если его нет то выдаёт первые элементы
    #options.add_argument('--disable-gpu')  # Отключаем GPU (рекомендуется для headless)
    #options.add_argument('--no-sandbox')  # Отключаем sandbox (нужно для некоторых Linux-серверов)
    service = Service(ChromeDriverManager().install())  # Автообновление драйвера
    driver = webdriver.Chrome(service=service, options=options) # Запускаем Chrome через Selenium
    #Получаем ФИО
    try:
        driver.get(url)  # Переходим по URL с сайта из QR-кода
        wait = WebDriverWait(driver, 10)  # Создаём ожидание до 10 секунд
        full_name_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.title")))  # Ждём появления элемента с ФИО
        full_name = full_name_elem.text.strip()  # Получаем текст ФИО
        #Получаем город
        try:
            city_elems = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.txt-opacity")))
            city = city_elems[-1].text if city_elems else "Город не найден"
        except:
            city = "Город не найден"
        #Получаем статус удостоверения
        try:
            status_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.lbl.center.lbl-g")))
            status = status_elem.text.strip()
        except:
            status = "Статус не найден"  # Если статус не найден, пишем дефолт
        #Получаем маршруты
        try:
            parent_hike_block = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".chapter.row-item.hike.is-open")))
            hike_block = parent_hike_block.find_elements(By.CSS_SELECTOR, "div.title")
            hikes = []
            for elem in hike_block:
                text = elem.text.strip()
                if text:
                    hikes.append(text)
                else: 
                    "Маршрут не найден"
        except:
            hikes = "Маршрут не найден"
        #Получаем походы
        try:
            parent_route_block = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".chapter.row-item.route.is-open")))
            route_block = parent_route_block.find_elements(By.CSS_SELECTOR, "div.title")        
            routes = []
            for elem in route_block:
                text = elem.text.strip()
                if text:
                    routes.append(text)
                else: 
                    "Поход не найден"
        except:
            hikes = "Поход не найден"

        return {"full_name": full_name, "city": city, "status": status, "hike": hikes, "route": routes}  # Возвращаем словарь с данными
    
    except Exception as e:
        print(f"Ошибка при парсинге: {e}"
              f"Проблема в qr_handler")  # Логируем ошибки при парсинге
        return None  # Возвращаем None при ошибке
    finally:
        driver.quit()  # Обязательно закрываем браузер

async def fetch_info_selenium(url: str) -> dict | None:
    loop = asyncio.get_running_loop()  # Получаем текущий цикл событий
    with ThreadPoolExecutor() as pool:  # Создаём пул потоков для блокирующего вызова
        result = await loop.run_in_executor(pool, fetch_info_selenium_sync, url)  # Запускаем синхронную функцию в пуле
    return result  # Возвращаем результат из потока

