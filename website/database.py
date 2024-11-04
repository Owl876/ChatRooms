from sqlalchemy import create_engine, Column, Integer, String,  ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Строка для указания параметров подключения к БД
DATABASE_URL = "postgresql://web_user:password@db:5432/web_database"

# Подключение к сервреу БД (создание движка)
engine = create_engine(DATABASE_URL)

# Базовый класс для всех моделей БД
Base = declarative_base()

# Создание нового экземпляра сессии для взаимодействий с БД
# Без автоматической фиксации обновлений, без автоматического обновления данных в БД перед 
# Также указываем созданное ранее подключение
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Получение сессии базы данных
def get_db():
    # Создание новой сессии для работы с БД
    db = SessionLocal()
    try:
        # Возвращение объекта сессии
        yield db
    finally:
        # В конечном итоге закрываем сессию
        db.close()

# Модель пользователя в базе данных (ORM-модель)
class Users(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    password = Column(String)

# Модель чата в базе данных (ORM-модель)
class Chats(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    owner = Column(String, ForeignKey("users.email"))