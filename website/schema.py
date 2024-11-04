from pydantic import BaseModel
from typing import Optional

# Модель пользователя при регистрации
class UserRegister(BaseModel):
    # Передаваемые значения либо строки, либо None
    email: Optional[str] = None 
    password: Optional[str] = None

# Модель пользователя при авторизации
class UserAuthorizate(BaseModel):
    email: Optional[str] = None 
    password: Optional[str] = None

# Модель токена
class Token(BaseModel):
    access_token: str
    token_type: str

# Модель запроса с передачей названия чата
class ChatRequest(BaseModel):
    chat_name: str

# Модель сообщения о выходе из аккаунта
class LogoutMessage(BaseModel):
    message: str