import requests
from test_utils import (generate_unique_email, generate_unique_chat_name, register_user, authorize_user,
                        authorize_user_with_token, create_chat)

BASE_URL = "http://127.0.0.1"  # URL запущенного сервера

# Тест регистрации пользователя
def test_registration():
    unique_email = generate_unique_email()
    register_user(unique_email, "password")

# Тест авторизации пользователя
def test_authorization():
    unique_email = generate_unique_email()
    register_user(unique_email, "password")
    authorize_user(unique_email, "password")

# Тест создания чата
def test_create_chat():
    unique_email = generate_unique_email()
    unique_chat_name = generate_unique_chat_name()

    # Сначала регистрируем и авторизуем пользователя
    register_user(unique_email, "password")
    session_token = authorize_user_with_token(unique_email, "password")

    # Создание чата
    create_chat(unique_chat_name, session_token)


# Тест поиска чатов
def test_search_chats():
    unique_email = generate_unique_email()
    unique_chat_name = generate_unique_chat_name()

    # Сначала регистрируем и авторизуем пользователя
    register_user(unique_email, "password")
    session_token = authorize_user_with_token(unique_email, "password")

    # Создание чата
    create_chat(unique_chat_name, session_token)

    # Теперь ищем чат по имени
    response = requests.get(f"{BASE_URL}/search/?query={unique_chat_name}")
    assert response.status_code == 200
    assert "chats" in response.json()


# Тест удаления чата
def test_delete_chat():
    unique_email = generate_unique_email()
    unique_chat_name = generate_unique_chat_name()

    # Сначала регистрируем и авторизуем пользователя
    register_user(unique_email, "password")
    session_token = authorize_user_with_token(unique_email, "password")

    # Создание чата
    create_chat(unique_chat_name, session_token)

    # Удаление чата
    response = requests.delete(f"{BASE_URL}/chats/{unique_chat_name}", cookies={"session": session_token})
    assert response.status_code == 200



# Тест выхода из аккаунта
def test_logout():
    unique_email = generate_unique_email()

    # Сначала регистрируем и авторизуем пользователя
    register_user(unique_email, "password")
    session_token = authorize_user_with_token(unique_email, "password")

    # Выход
    response = requests.get(f"{BASE_URL}/logout/", cookies={"session": session_token})
    assert response.status_code == 200
