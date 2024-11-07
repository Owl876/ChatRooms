from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database import Users, get_db
from jose import JWTError, jwt

# Конфигурация JWT
SECRET_KEY = "very_very_secret_key"
ALGORITHM = "HS256"
TOKEN_LIFETIME_MINUTES = 240

# Генерация JWT токена
def generate_access_token(data: dict, expiry: timedelta = None) -> str:

    data_to_encode = data.copy()
    expiration_time = datetime.now() + (expiry or timedelta(minutes=TOKEN_LIFETIME_MINUTES))
    data_to_encode.update({"exp": expiration_time})

    return jwt.encode(data_to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Возвращает текущего авторизованного пользователя, используя JWT токен из сессии.
def get_current_user(request: Request, db: Session = Depends(get_db)) -> Users:

    token = request.session.get('token')
    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Проверка подлинности пользователя не удалась",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise auth_error

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("email")
        if not user_email:
            raise auth_error
    except JWTError:
        raise auth_error

    user = db.query(Users).filter(Users.email == user_email).first()
    if not user:
        raise auth_error

    return user

# Проверяет, авторизован ли пользователь, расшифровывая JWT токен из сессии.
def is_user_authenticated(request: Request, db: Session = Depends(get_db)) -> bool:

    token = request.session.get('token')
    if not token:
        return False
    
    # Расшифровываем токен
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("email")
        user = db.query(Users).filter(Users.email == user_email).first()
        return user is not None
    except JWTError:
        return False

# Извлекает данные (email пользователя или название чата) из JWT токена.
def get_current_item(token: str, return_type: str, db: Session = Depends(get_db)) -> str:
    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Ошибка аутентификации",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise auth_error

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("email")
        chat_name = payload.get("chat")
        if not email or (return_type == "chat" and not chat_name):
            raise auth_error
    except JWTError:
        raise auth_error

    user = db.query(Users).filter(Users.email == email).first()
    if not user:
        raise auth_error

    return email if return_type == "email" else chat_name
