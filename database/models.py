from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Boolean, ForeignKey #типы данных и колонки для таблиц
from datetime import datetime, timezone
from sqlalchemy.orm import relationship #для связи таблиц(инструктор - история обновлений)
from database.base import Base #базовый класс для наследования
from passlib.context import CryptContext #для хеширования и проверки паролей

class Instructor(Base):
    __tablename__ = "instructors" #имя таблицы в базе

    id = Column(Integer, primary_key=True, index=True) #уникальный id (первичный ключ)
    # Личная информация
    last_name = Column(String, nullable=False) #nullable=False поле обязательно для заполнения
    first_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=True) #отчество может быть null
    birth_date = Column(Date, nullable=False)
    gender = Column(String, nullable=False)  # Можно Enum, если хочешь строгость

    # Контакты
    email = Column(String, unique=True, nullable=False) #unique=True уникальное значение
    phone = Column(String, nullable=False)

    #Желаемая дата экзамена
    desired_exam_date = Column(Date, nullable=True)

    # Подвиды маршрутов в формате чекбокса
    rock_routes = Column(String, default=False)
    snow_routes = Column(String, default=False)
    ice_routes = Column(String, default=False)
    mixed_routes = Column(String, default=False)
    high_altitude_routes = Column(String, default=False)
    ski_routes = Column(String, default=False)

    # Строка с категорией сложности (IV, V и тп)
    difficulty_category = Column(String)

    # Паспортные данные
    passport_type = Column(String, nullable=True)  # РФ или другой
    passport_number = Column(String, nullable=True)
    passport_issued_by = Column(String, nullable=True)
    passport_unit_code = Column(String, nullable=True)
    passport_issue_date = Column(Date, nullable=True)

    passport_scan_main = Column(String, nullable=True) #путь до файла
    passport_scan_registration = Column(String, nullable=True)

    # Альтернативный документ
    other_id_document_name = Column(String, nullable=True)
    other_id_document_scan = Column(String, nullable=True)

    # Прописка и адрес
    postal_index = Column(String, nullable=True)
    registration_address = Column(String, nullable=True)
    actual_address = Column(String, nullable=True)

    # Идентификационные данные
    snils = Column(String, nullable=True)
    inn = Column(String, nullable=True)
    photo = Column(String, nullable=True)  # Фото для удостоверения

    history = relationship("ChangeHistory", back_populates="instructor", cascade="all, delete")


class ChangeHistory(Base):
    __tablename__ = "change_history"

    id = Column(Integer, primary_key=True, index=True)
    #Уникальный ID записи об изменении
    instructor_id = Column(Integer, ForeignKey("instructors.id", ondelete="CASCADE"), nullable=False)
    #ID инструктора, к которому относится изменение (внешний ключ к таблице instructors)
    changed_by = Column(String, nullable=False)  #кто внёс изменение email или "admin"
    change_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    #Когда произошло изменение
    field_name = Column(String, nullable=False)  # Название изменённого поля
    old_value = Column(Text, nullable=True)  # Предыдущее значение (до изменения)
    new_value = Column(Text, nullable=True)  # Новое значение (после изменения)

    instructor = relationship("Instructor", back_populates="history")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    _password = Column("password", String, nullable=False)  # храним как защищённое поле

    # Геттер запрещает читать пароли напрямую
    @property
    def password(self):
        raise AttributeError("Пароль нельзя прочитать напрямую")
    #Сеттер позволяет задать пароль обычной строкой и он будет автоматически захеширован
    @password.setter
    def password(self, plain_password):
        self._password = pwd_context.hash(plain_password)

    # ✅ метод для проверки пароля при входе
    def verify_password(self, plain_password):
        return pwd_context.verify(plain_password, self._password)
