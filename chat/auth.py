from fastapi import HTTPException, status
from jose import JWTError, jwt
from typing import Optional

# Конфигурация для JWT
SECRET_KEY = "donut_loves_AC/DC"
ALGORITHM = "HS256"

# Исключение для неверных учетных данных
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Ошибка проверки подлинности пользователя",
    headers={"WWW-Authenticate": "Bearer"},
)

# Функция для извлечения email или названия чата из токена
def get_current_item(token: str, return_type: str) -> Optional[str]:
    if not token:
        raise credentials_exception

    try:
        # Декодирование токена
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Извлечение данных из токена
        email = payload.get("email")
        chat = payload.get("chat")

        # Проверка наличия данных в токене
        if return_type == "email" and email:
            return email
        elif return_type == "chat" and chat:
            return chat
        else:
            raise credentials_exception

    except JWTError:
        raise credentials_exception
