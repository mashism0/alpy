import os
from dotenv import load_dotenv # Для загрузки переменных окружения из .env файла
from logging.config import fileConfig #Для конфигурации логгирования
from sqlalchemy import engine_from_config, pool#Для создания движка SQLAlchemy и управления пулом соединений
from alembic import context # Основной объект Alembic для конфигурации и запуска миграций

load_dotenv()

# Получаем объект конфигурации Alembic из env.py
config = context.config

# Настраиваем логгирование, если указано имя конфигурационного файла
if config.config_file_name is not None:
    fileConfig(config.config_file_name)  # Загружаем настройки логгирования из .ini-файла Alembic

    # Ниже настраивается более красивый формат логирования в цвете (если установлен colorlog)
    import logging
    from colorlog import ColoredFormatter

    # Настраиваем формат вывода логов с цветами для разных уровней сообщений
    formatter = ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(white)s[%(name)s]%(reset)s %(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    )

    # Создаём обработчик логов, применяем форматтер
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    # Назначаем обработчик корневому логгеру
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.INFO)  # Можно сменить на DEBUG для более подробных логов

# Импорт моделей SQLAlchemy, чтобы Alembic мог "видеть" схемы таблиц и отслеживать изменения
import sys

# Добавляем путь к приложению в sys.path, чтобы можно было делать абсолютные импорты
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Импортируем базу и модели
from database.base import Base  # Base.metadata будет использоваться для генерации миграций
from database import models     # Импорт всех моделей (даже если они не используются явно — чтобы Alembic их увидел)

# Указываем Alembic, какую метаинформацию использовать (например, для auto-migrate)
target_metadata = Base.metadata

# Функция возвращает URL подключения к базе данных, заменяя asyncpg на psycopg2
# Это важно, так как Alembic работает только в синхронном контексте
def get_url():
    return os.getenv("DATABASE_URL").replace("asyncpg", "psycopg2")

# Настройка и запуск миграций в "оффлайн-режиме"
# Этот режим не требует подключения к базе данных, просто генерирует SQL
def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,  # Метаданные для автогенерации миграций
        literal_binds=True,               # Вставлять значения прямо в SQL, без параметров
        dialect_opts={"paramstyle": "named"},  # Стиль параметров в SQL
    )
    with context.begin_transaction():  # Начинаем транзакцию миграции
        context.run_migrations()       # Запускаем миграции

# Настройка и запуск миграций в "онлайн-режиме"
# Этот режим требует активного соединения с БД
def run_migrations_online():
    # Создаём движок SQLAlchemy с передачей URL напрямую (чтобы не брать его из alembic.ini)
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),  # Читаем конфигурацию Alembic
        prefix='sqlalchemy.',                           # Префикс ключей в alembic.ini
        poolclass=pool.NullPool,                        # Отключаем пул соединений (не нужен для Alembic)
        url=get_url(),                                  # Передаём URL подключения
    )

    # Подключаемся к БД
    with connectable.connect() as connection:
        # Конфигурируем Alembic с открытым соединением и метаданными
        context.configure(connection=connection, target_metadata=target_metadata)

        # Выполняем миграции в транзакции
        with context.begin_transaction():
            context.run_migrations()

# Определяем какой режим использовать — оффлайн или онлайн
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()










# Загружаем переменные окружения из файла `.env`
# Это позволяет держать параметры подключения (например, URL к БД) вне кода
# load_dotenv()
# print("DATABASE_URL:", os.getenv("DATABASE_URL"))
# config = context.config



# if config.config_file_name is not None:
#     fileConfig(config.config_file_name)

# config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL").replace("asyncpg", "psycopg2"))
# target_metadata = Base.metadata



# def run_migrations_offline() -> None:
#     url = config.get_main_option("sqlalchemy.url")
#     context.configure(
#         url=url,
#         target_metadata=target_metadata,
#         literal_binds=True,
#         dialect_opts={"paramstyle": "named"},
#     )

#     with context.begin_transaction():
#         context.run_migrations()


# def run_migrations_online() -> None:
#     connectable = engine_from_config(
#         config.get_section(config.config_ini_section, {}),
#         prefix="sqlalchemy.",
#         poolclass=pool.NullPool,
#     )

#     with connectable.connect() as connection:
#         context.configure(
#             connection=connection, target_metadata=target_metadata
#         )

#         with context.begin_transaction():
#             context.run_migrations()


# if context.is_offline_mode():
#     run_migrations_offline()
# else:
#     run_migrations_online()
