FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Открываем чат для внешних подключений на порту 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]