import random
import string
import requests

BASE_URL = "http://127.0.0.1"  # URL запущенного сервера

# Генерация уникальных данных для тестов
def generate_unique_email():
    return f"testuser{random.randint(1000, 9999)}@example.com"

def generate_unique_chat_name():
    return "Test_Chat_" + ''.join(random.choices(string.ascii_letters + string.digits, k=6))


# Функция для регистрации пользователя
def register_user(email, password):
    response = requests.post(f"{BASE_URL}/registration/", data={
        "email": email,
        "password": password
    })
    assert response.status_code == 200
    assert "Аккаунт успешно зарегистрирован" in response.text

# Функция для авторизации пользователя и получения токена
def authorize_user(email, password):
    response = requests.post(f"{BASE_URL}/authorization/", data={
        "email": email,
        "password": password
    })
    assert response.status_code == 200

# Функция для авторизации пользователя и получения токена
def authorize_user_with_token(email, password):
    response = requests.post(f"{BASE_URL}/authorization/", data={
        "email": email,
        "password": password
    })
    assert response.status_code == 200
    session_token = response.cookies.get("session")
    assert session_token is not None
    return session_token

def create_chat(chat_name, session_token):
    # Создание чата, передаем cookie с токеном сессии
    cookies = {"session": session_token}
    response = requests.post(f"{BASE_URL}/chats/", data={
        "name": chat_name
    }, cookies=cookies)

    # Проверка результата создания чата
    assert response.status_code == 200
    assert "Чат создан" in response.text