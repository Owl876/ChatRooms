from passlib.context import CryptContext

# Объект контекста, указываем алгоритм хэширования bcrypt
# Указываем, что если схема хэширования устареет, то она автоматически помечается как устаревшая
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Функция для хэширования пароля
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Функция проверки, соответствует ли передаваемый пароль хэшированному паролю
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)