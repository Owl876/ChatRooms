from sqlalchemy import create_engine, Column, Integer, String,  ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://web_user:password@db:5432/web_database"

engine = create_engine(DATABASE_URL)

# Базовый класс для всех моделей БД
Base = declarative_base()

# Создание нового экземпляра сессии для взаимодействий с БД
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Получение сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
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