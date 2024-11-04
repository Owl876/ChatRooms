from fastapi import HTTPException, status
from jose import JWTError, jwt

# Секретный ключ для JWT шифрования
SECRET_KEY = "very_very_secret_key"
ALGORITHM = "HS256"

# Функция для получения email пользователя или названия чата из токена 
def get_current_item(token: str, type_return: str) -> str:
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
    
    # В зависимости от второго аргумента функции возвращаем либо email, либо название чата
    if (type_return == "email"):
        return email
    elif (type_return == "chat"):
        return chat
    else:
        return None