FROM python:3.9

# Рабочая директория
WORKDIR /app
# Копируем файл requirements
COPY requirements.txt .
# Устанавливаем модули python, не сохраняем кэшированные пакеты, указываем файл с именами модулей
RUN pip install --no-cache-dir -r requirements.txt
# Копируем все файлы из директории ./chat в рабочую директорию проекта 
COPY . .
# Команда при запуске контейнера
# С помощью uvicorn запускаем приложение в main_chat, открываем для внешних подключений (т.к. хост 0.0.0.0) на порте 8001
CMD ["uvicorn", "main_chat:app", "--host", "0.0.0.0", "--port", "8001"]