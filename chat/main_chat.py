from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List, Tuple
import json
from auth import get_current_item

app = FastAPI()

# Хранилище для подключения пользователей к чату
class ConnectionManager:
    # При инициализации менеджера, создаем список кортежей, содержащих соединения и имена чатов
    def __init__(self):
        self.active_connections: List[Tuple[WebSocket, str]] = []

    # Функция установления соединения
    # Сперва подреждает и устанавливает соединение, переданное через websocket
    # Далее добавляет информацию о соединении и комнате в список active_connections
    async def connect(self, websocket: WebSocket, chat_name: str):
        await websocket.accept()
        self.active_connections.append((websocket, chat_name))

    # Функция для обновления комнаты в текущем соединении
    async def update_chat_for_connection(self, websocket: WebSocket, new_chat: str):
        for index, (connection, chat) in enumerate(self.active_connections):
            if connection == websocket:
                self.active_connections[index] = (connection, new_chat)
                break

    # Функция удаления соединения из списка активных соединений
    # В списке остаются только соединения, которые не совпадают с переданным
    def disconnect(self, websocket: WebSocket):
        self.active_connections = [conn for conn in self.active_connections if conn[0] != websocket]

    # Функция отправки сообщения в конкретный чат
    async def send_message_to_chat(self, chat_name: str, message: str):
        for connection, chat in self.active_connections:
            if chat == chat_name:
                await connection.send_text(message)

# Инициализируем менеджера для управления подключениями WebSocket
manager = ConnectionManager()

# Маршрут для обработки WebSocket соединения
@app.websocket("/ws/chat/")
async def websocket_endpoint(websocket: WebSocket):
    # Подключение к WebSocket через менеджера
    await manager.connect(websocket, "")

    # Информация о чате и пользователь текущего соединения
    chat = ""
    user = ""

    try:
        while True:
            # Получение сообщение из соединение и преобразование JSON в словарь
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # При установке соединения
            if message_data["type"] == "auth":
                # Получаем email пользователя и название чата из JWT токена
                user = get_current_item(message_data["token"], "email")
                chat = get_current_item(message_data["token"], "chat")
                # Сообщение о том, что пользователь подключился к комнате
                if user and chat:
                    await manager.update_chat_for_connection(websocket, chat)
                    await manager.send_message_to_chat(chat, f"Пользователь {user} успешно подключился к комнате {chat}")
                else:
                    await manager.send_message_to_chat("Ошибка подключения")

            # При отправке сообщения
            elif message_data["type"] == "send":
                # Отправка сообщения от пользователя
                message = message_data["message"]
                await manager.send_message_to_chat(chat, f"Пользователь {user} сказал: {message}")

    # Обработка исключения при отключении пользователя
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.send_message_to_chat(chat, f"Пользователь {user} покинул чат")