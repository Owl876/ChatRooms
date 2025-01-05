// Формируем URL динамически
const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
const host = window.location.host; // Домен текущего хоста
const socketUrl = `${protocol}//${host}/ws/chat/`;
const socket = new WebSocket(socketUrl);

const token = localStorage.getItem("token");

// При открытии соединения
socket.onopen = function() {
    const authMessage = {
        type: "auth",
        token: token
    };
    socket.send(JSON.stringify(authMessage));
};

// Получение сообщений
socket.onmessage = function(event) {
    const chatBox = document.getElementById("chat-box");
    chatBox.innerHTML += "<p class='message'>" + event.data + "</p>";
    chatBox.scrollTop = chatBox.scrollHeight; // Прокручиваем вниз
};

// Функция для отправки сообщений
function sendMessage() {
    const input = document.getElementById("messageInput");
    const message = input.value.trim();

    if (message) {
        socket.send(JSON.stringify({ type: "send", message: message }));
        input.value = ""; // Очищаем поле ввода
    }
}

// Отправка сообщения по клавише Enter
document.getElementById("messageInput").addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});