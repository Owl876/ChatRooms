FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "sleep 10 && uvicorn main:app --host 0.0.0.0 --port 8001"]
# sleep 10 необходим для первого запуска, чтобы успеть полностью поднять базу данных
# в дальнейшем можно использовать следующий вариант:
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]