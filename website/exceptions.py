from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import Users
from auth import generate_access_token
import re

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Функция для хеширования пароля
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Функция проверки, соответствует ли передаваемый пароль хэшированному паролю
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Проверка корректности email по шаблону
def is_valid_email(email: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

# Проверка, что все поля заполнены
def are_fields_filled(user) -> bool:
    return user.email is not None and user.password is not None

# Проверка, существует ли пользователь в базе данных
def is_user_exist(db: Session, email: str) -> bool:
    return db.query(Users).filter(Users.email == email).first() is not None

# Создание нового пользователя в базе данных
def create_new_user(db: Session, email: str, password: str):
    user_count = db.query(Users).count()
    new_user = Users(id=user_count, email=email, password=get_password_hash(password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

# Создание JWT токена с информацией о пользователе и чате.
def generate_token_for_chat(user_email: str, chat_name: str):
    token_data = {"email": user_email, "chat": chat_name}
    return generate_access_token(data=token_data)