import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from test_utils import generate_unique_email, generate_unique_chat_name, register_user

unique_email = generate_unique_email()
chat_name = generate_unique_chat_name()

@pytest.fixture
def driver():
    driver = webdriver.Chrome()
    yield driver
    driver.quit()

def test_registration_and_chat(driver):
    driver.get("http://127.0.0.1/")

    # Регистрация
    driver.find_element(By.LINK_TEXT, "Зарегистрироваться").click()
    driver.find_element(By.NAME, "email").send_keys(unique_email)
    driver.find_element(By.NAME, "password").send_keys("password")
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    # Авторизация
    # driver.find_element(By.LINK_TEXT, "Перейти на страницу авторизации").click()
    # driver.find_element(By.NAME, "email").send_keys(unique_email)
    # driver.find_element(By.NAME, "password").send_keys("password")
    # driver.find_element(By.XPATH, "//button[@type='submit']").click()

    # Создание чата
    # driver.find_element(By.LINK_TEXT, "Перейти к чатам").click()
    driver.find_element(By.NAME, "name").send_keys(chat_name)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    # Поиск чата
    driver.find_element(By.NAME, "query").send_keys(chat_name)
    time.sleep(1)

    # Вход в чат
    driver.find_element(By.XPATH, "//button[contains(text(), 'Войти в чат')]").click()
    time.sleep(1)

    # Отправка сообщения в чат
    driver.find_element(By.ID, "messageInput").send_keys("Hello, world!")
    driver.find_element(By.XPATH, "//button[contains(text(), 'Send')]").click()

    time.sleep(2)


# Тест неудачной регистрации, когда пользователь уже существует
def test_registration_user_exists(driver):
    unique_email = generate_unique_email()  # генерируем уникальный email
    register_user(unique_email, "password")  # Регистрация первого пользователя

    # Пытаемся зарегистрировать того же пользователя
    driver.get("http://127.0.0.1/registration/")
    driver.find_element(By.NAME, "email").send_keys(unique_email)  # Тот же email
    driver.find_element(By.NAME, "password").send_keys("password")
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    # Проверка сообщения об ошибке
    error_message = driver.find_element(By.XPATH, "//div[contains(text(), 'Аккаунт с таким email уже существует')]").text
    assert "Аккаунт с таким email уже существует" in error_message


# Тест неудачной авторизации с неверным email
def test_authorization_invalid_email(driver):
    driver.get("http://127.0.0.1/authorization/")

    driver.find_element(By.NAME, "email").send_keys("invalid-email@gmail.com")  # Некорректный email
    driver.find_element(By.NAME, "password").send_keys("password")
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    # Проверка сообщения об ошибке
    error_message = driver.find_element(By.XPATH, "//div[contains(text(), 'Неверные данные')]").text
    assert "Неверные данные" in error_message


# Тест неудачной авторизации с неверным паролем
def test_authorization_invalid_password(driver):
    unique_email = generate_unique_email()  # генерируем уникальный email
    register_user(unique_email, "password")  # Регистрация пользователя

    driver.get("http://127.0.0.1/authorization/")
    driver.find_element(By.NAME, "email").send_keys(unique_email)
    driver.find_element(By.NAME, "password").send_keys("wrongpassword")  # Неверный пароль
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    # Проверка сообщения об ошибке
    error_message = driver.find_element(By.XPATH, "//div[contains(text(), 'Неверные данные')]").text
    assert "Неверные данные" in error_message
