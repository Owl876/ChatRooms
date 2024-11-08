from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List, Tuple, Optional
import json
from auth import get_current_item

app = FastAPI()

# Класс для управления активными соединениями WebSocket
class ConnectionManager:
    def __init__(self):
        # Список активных соединений и их чатов
        self.active_connections: List[Tuple[WebSocket, str]] = []

    # Установка нового соединения и добавление его в список активных
    async def connect(self, websocket: WebSocket, chat_name: str):
        await websocket.accept()
        self.active_connections.append((websocket, chat_name))

    # Обновление чата для указанного соединения
    async def update_chat_for_connection(self, websocket: WebSocket, new_chat: str):
        self.active_connections = [
            (conn, new_chat) if conn == websocket else (conn, chat)
            for conn, chat in self.active_connections
        ]

    # Удаление соединения из списка активных
    def disconnect(self, websocket: WebSocket):
        self.active_connections = [
            (conn, chat) for conn, chat in self.active_connections if conn != websocket
        ]

    # Отправка сообщения всем соединениям в указанном чате
    async def send_message_to_chat(self, chat_name: str, message: str):
        for connection, chat in self.active_connections:
            if chat == chat_name:
                await connection.send_text(message)

# Создаем экземпляр ConnectionManager для управления соединениями
manager = ConnectionManager()

# Проверка и извлечение email и chat из токена.
async def authenticate_user(websocket: WebSocket, token: str) -> Optional[Tuple[str, str]]:
    user = get_current_item(token, "email")
    chat = get_current_item(token, "chat")
    if user and chat:
        return user, chat
    else:
        await websocket.send_text("Ошибка: не удалось подключиться")
        return None

async def handle_authentication(websocket: WebSocket, token: str) -> Optional[str]:
    """Аутентифицирует пользователя и обновляет его соединение с чатом."""
    user_data = await authenticate_user(websocket, token)
    if user_data:
        user, chat = user_data
        await manager.update_chat_for_connection(websocket, chat)
        await manager.send_message_to_chat(chat, f"{user} присоединился к чату {chat}")
        return chat
    return None

async def handle_message(websocket: WebSocket, chat: str, user: str, message: str):
    """Отправляет сообщение от пользователя в указанный чат."""
    if chat:
        await manager.send_message_to_chat(chat, f"{user} сказал: {message}")
    else:
        await websocket.send_text("Ошибка: сообщение не отправлено. Вы не подключены к чату.")

# WebSocket маршрут для чатов
@app.websocket("/ws/chat/")
async def websocket_endpoint(websocket: WebSocket):
    # Подключение к WebSocket через менеджера
    await manager.connect(websocket, "")

    # Информация о чате и пользователь текущего соединения
    chat = ""
    user = ""

    try:
        while True:
            # Получение и парсинг сообщения из WebSocket
            data = await websocket.receive_text()
            message_data = json.loads(data)
            message_type = message_data.get("type")

            if message_type == "auth":
                token = message_data.get("token")
                chat = await handle_authentication(websocket, token)
                user = get_current_item(token, "email")
            elif message_type == "send":
                message = message_data.get("message")
                await handle_message(websocket, chat, user, message)

    # Обработка исключения при отключении пользователя
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.send_message_to_chat(chat, f"Пользователь {user} покинул чат")