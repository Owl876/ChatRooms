from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database import Users, get_db
from jose import JWTError, jwt

# Секретный ключ для JWT шифрования
SECRET_KEY = "very_very_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 240

# Функция для создания JWT токена
def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    # Данные для шифрования
    to_encode = data.copy()
    
    # Установка времени истечения действия токена (по умолчанию ACCESS_TOKEN_EXPIRE_MINUTES)
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Добавляем в словарь to_encode ключ exp, который указывает время истечения действия токена
    to_encode.update({"exp": expire})

    # Кодируем токен
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Функция для получения модели авторизованного пользователя
def get_current_user(request: Request, db: Session = Depends(get_db)) -> Users:
    # Исключение, вызываемое в случае, если не удалось подтвердить подленность пользователя
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Ошибка проверки подленности пользователя",
        headers={"Authorization": "Bearer"},
    )

    # Получаем токен из сессии
    token = request.session.get('token')

    # Если токена в сессии нет
    if token is None:
        raise credentials_exception
    
    # Декодируем токен, извлекаем email
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("email")
        # Если поле email отсутствует в токене
        if email is None:
            raise credentials_exception
    # Случай ошибок при декодировании токена (например, поддельный токен)
    except JWTError:
        raise credentials_exception

    # Извлекаем из БД пользователям с полученным email
    user = db.query(Users).filter(Users.email == email).first()

    if user is None:
        raise credentials_exception

    return user

# Проверка с помощью токена, авторизован ли такой пользователь в системе
def is_user_authorizate(request: Request, db: Session = Depends(get_db)) -> Users:
    # Получаем токен из сессии
    token = request.session.get('token')

    # Если токена в сессии нет
    if token is None:
        return False
    
    # Если токен есть, расшифровываем его
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Получаем email пользователя из токена
        email: str = payload.get("email")

        # Поиск в базе данных пользователя с таким email
        user = db.query(Users).filter(Users.email == email).first()

        if user is None:
            return False

        return True
    
    # Обработка ошибки обработки токена
    except JWTError:
        return False

# Функция для получения email пользователя или названия чата из токена 
def get_current_item(token: str, type_return: str, db: Session = Depends(get_db)) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Ошибка проверки подленности пользователя",
        headers={"Authorization": "Bearer"},
    )

    if token is None:
        raise credentials_exception
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Получаем email из токена
        email: str = payload.get("email")
        if email is None:
            raise credentials_exception
        # Получаем название чата из токена
        chat: str = payload.get("chat")
        if chat is None:
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception

    user = db.query(Users).filter(Users.email == email).first()
    if user is None:
        raise credentials_exception
    
    # В зависимости от второго аргумента функции возвращаем либо email, либо название чата
    if (type_return == "email"):
        return email
    elif (type_return == "chat"):
        return chat
    else:
        return None