async function getTokenAndRedirect(chatName) {
    try {
        const response = await fetch('/get_token_for_chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ "chat_name": chatName }),
        });

        const data = await response.json();
        if (response.ok) {
            const token = data.access_token;
            localStorage.setItem("token", token);
            window.location.href = "/meeting_room/";
        } else {
            console.error('Error getting token:', data.detail);
        }
    } catch (error) {
        console.error('Request failed', error);
    }
}

async function deleteChat(chatName) {
    const confirmed = confirm("Вы уверены, что хотите удалить этот чат?");
    if (!confirmed) return;

    const response = await fetch(`/chats/${chatName}`, {
        method: "DELETE"
    });

    if (response.ok) {
        document.getElementById(`chat-${chatName}`).remove();
        document.getElementById(`button1-${chatName}`).remove();
        document.getElementById(`button2-${chatName}`).remove();
    } else {
        alert("Ошибка при удалении чата");
    }
}

async function logout() {
    localStorage.removeItem("token");

    try {
        const response = await fetch('/logout/');
        if (response.ok) {
            window.location.href = '/'; // Перенаправление на главную страницу после выхода
        } else {
            console.error("Не удалось выйти из аккаунта");
        }
    } catch (error) {
        console.error("Ошибка выхода:", error);
    }
}

async function searchChats() {
    const searchInput = document.getElementById('search');
    const query = searchInput.value;
    const resultsContainer = document.getElementById('results-container');

    // Скрываем результаты, если менее 6 символов
    if (query.length < 6) {
        resultsContainer.innerHTML = ''; // Очищаем контейнер
        return;
    }

    try {
        const response = await fetch(`/search/?query=${encodeURIComponent(query)}`);
        const data = await response.json();

        resultsContainer.innerHTML = ''; // Очищаем предыдущие результаты

        if (data.chats && data.chats.length > 0) {
            const ul = document.createElement('ul');
            data.chats.forEach(chat => {
                const li = document.createElement('li');
                li.textContent = chat.name;
                li.onclick = () => getTokenAndRedirect(chat.name);
                ul.appendChild(li);
            });
            resultsContainer.appendChild(ul);
        } else {
            const noResultsLi = document.createElement('li');
            noResultsLi.textContent = 'Чатов с таким названием не найдено.';
            resultsContainer.appendChild(noResultsLi);
        }
    } catch (error) {
        console.error('Ошибка при поиске чатов:', error);
    }
}
