from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
#DeclarativeBase позволяет взаимодействовать с данными как с объектами Python,
#не задействуя SQL напрямую