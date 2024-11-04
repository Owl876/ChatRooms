function logout() {
    // Удаление токена из localStorage
    localStorage.removeItem('token');
    // Удаление токена из сессии через запрос на маршрут /logout/
    fetch('/logout/')
        .then(response => {
            if (response.ok) {
                window.location.href = '/'; // Перенаправление на главную страницу
            } else {
                console.log("Не удалось выйти из аккаунта");
            }
        })
        .catch(error => console.error('Ошибка выхода:', error));
}