FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# С помощью uvicorn запускаем приложение в main_chat, открываем для внешних подключений (т.к. хост 0.0.0.0) на порте 8001
CMD ["uvicorn", "main_chat:app", "--host", "0.0.0.0", "--port", "8001"]