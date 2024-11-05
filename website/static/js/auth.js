// Функция для выхода из аккаунта
async function logout() {
    // Удаление токена из localStorage и сессии
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