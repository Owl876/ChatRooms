from fastapi import FastAPI, Request, Form, Depends, HTTPException, Response
from sqlalchemy.orm import Session 
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from database import engine, Base, get_db 
from database import Users, Chats 
from schema import UserRegister, UserAuthorizate, Token, ChatRequest, LogoutMessage
from utils import get_password_hash, verify_password
from auth import create_access_token, get_current_user, is_user_authorizate
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
import re

# Методля создания всех таблиц в БД, в параметере указывается конкретное соединение с БД
Base.metadata.create_all(bind=engine)

# Создание экземпляра класса (основной объект) для работы с FastAPI 
app = FastAPI()

# Добавление промежуточного ПО для управлением сессиями в приложении, секретный ключ для шифрования данных сессии
app.add_middleware(SessionMiddleware, secret_key="your_secret_key")

# Добавление возможности рендеринга HTML-шаблонов с помощью Jinja2, в аргументе указывается директория с шаблонами 
templates = Jinja2Templates(directory="templates")

# Преобразованием данных из форм регистрации в модель пользователя при регистрации
async def getUserRegister(email: str = Form(None), password: str = Form(None)) -> UserRegister:
    return UserRegister(email=email, password=password)

# Преобразованием данных из форм авторизации в модель пользователя при авторизации
async def getUserAuthorizate(email: str = Form(None), password: str = Form(None)) -> UserAuthorizate:
    return UserAuthorizate(email=email, password=password)

# Создание токена, содержащего информацию об авторизованном пользователе и чате, в который входит пользователь
def generate_token_for_chat(user_email: str, chat_name: str):
    token_data = {"email": user_email, "chat": chat_name}
    return create_access_token(data=token_data)

# Маршрут для регистрации
# В качестве ответа указывается тип ответа HTMLResponse (для отрисовки шаблона)
# В обработчик передается объект Request, содержащий информацию о запросе клиента (URL запроса, параметры, заголовки и т.д.)
@app.api_route("/register/", methods=["GET", "POST"], response_class=HTMLResponse)
async def register(request: Request, db: Session = Depends(get_db), user: UserRegister = Depends(getUserRegister)):
    # Обработка POST-запроса
    if request.method == "POST":
        # Проверка, соответствует ли введенный email стандартному виду email
        valid = re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', user.email)
        # Если email корректен
        if valid:
            # Если одно из полей ввода пусто
            if user.email == None or user.password == None:
                return templates.TemplateResponse("register.html", {"request": request, "message": "Ошибка ввода"})

            # Поиск пользователя в базе данных
            db_user = db.query(Users).filter(Users.email == user.email).first()

            # Если пользователь с таким email уже зарегестрирован в системе
            if db_user: 
                return templates.TemplateResponse("register.html", {"request": request, "message_bad": "Аккаунт с таким email уже существует"})

            # Добавление зарегестрированного аккаунта в базу данных
            user_count = db.query(Users).count() 
            new_user = Users(id = user_count, email=user.email, password = get_password_hash(user.password))
            db.add(new_user)
            db.commit()
            # Обнолвение объекта new_user данными из базы данных (на случай автоматического заполнения полей в БД)
            db.refresh(new_user)

            return templates.TemplateResponse("register.html", {"request": request, "message_good": "Аккаунт успешно зарегестрирован"})
        
        # Если email введен некорректно
        else:
            return templates.TemplateResponse("register.html", {"request": request, "message_bad": "Email введен некорректно"})
    
    # Работа в случае GET запроса
    else:
        return templates.TemplateResponse("register.html", {"request": request})

# Маршрут для GET запрос на страницу авторизации
@app.get("/authorizate/", response_class=HTMLResponse)
def authorizate(request: Request, is_authorizate: bool = Depends(is_user_authorizate)):
    # Если пользователь уже авторизован, происходит перенаправление на страницу с управлением чатами
    if (is_authorizate):
        return RedirectResponse(url="/chats/")
    
    #Если пользователь не авторизован, то отрисовывается страница авторизации
    return templates.TemplateResponse("authorizate.html", {"request": request})

# Маршрут для POST запроса на страницу авторизации
@app.post("/authorizate/", response_class=HTMLResponse)
def authorizate(response: Response, request: Request, form_data: UserAuthorizate = Depends(getUserAuthorizate), db: Session = Depends(get_db)):
    # Поиск пользователя в БД с email, полученным из формы
    user = db.query(Users).filter(Users.email == form_data.email).first() 
        
    # Если пользователя с таким email нет в БД
    if not user:
        return templates.TemplateResponse("authorizate.html", {"request": request, "message_no": "Пользователя с таким логином не существует"})
    
    # Проверка корректности пароля
    if not verify_password(form_data.password, user.password):
        return templates.TemplateResponse("authorizate.html", {"request": request, "message_no": "Неверный пароль"})

    # Генерация JWT-токена и сохранения в сессии
    access_token = create_access_token(data={"email": user.email})
    request.session['token'] = access_token  
    return templates.TemplateResponse("authorizate.html", {"request": request, "message_yes": "Успешный вход", "token": access_token})

# Маршрут для GET запроса на страницу с чатами
@app.get("/chats/", response_class=HTMLResponse)
def chats_get(request: Request, message_type: str = None, current_user: Users = Depends(get_current_user), db: Session = Depends(get_db)):
    # Получаем список чатов, созданных данным пользователем, для отображения на странице
    chats = db.query(Chats).filter(Chats.owner == current_user.email).all()

    # Отображение сообщений об ошибке
    message = None
    if (message_type == "1"):
        message = "Длина названия чата должна быть более 6 символов"
    elif (message_type == "2"):
        message = "Чат с таким названием уже существует"
    elif (message_type == "3"):
        message = "Чат успешно создан"
    else:
        message = None
    return templates.TemplateResponse("chats.html", {"request": request, "chats": chats, "message": message})

# Маршрут для POST запроса на страницу с чатами (для добавления нового пользователя)
@app.post("/chats/", response_class=RedirectResponse)
def chats_post(request: Request, name: str = Form(None), db: Session = Depends(get_db), current_user: Users = Depends(get_current_user)):
    # Можно создавать чаты с длиной названия от 6 символов
    if len(name) < 6:
        return RedirectResponse(url="/chats/?message_type=1", status_code=303)
    
    # Если чат с таким названием уже существует
    chat = db.query(Chats).filter(Chats.name == name).first()
    if chat:
        return RedirectResponse(url="/chats/?message_type=2", status_code=303)
    
    # Создаем новую модель чата для добавления
    count_chat = db.query(Chats).count()
    new_chat = Chats(id = count_chat, name = name, owner = current_user.email)
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return RedirectResponse(url="/chats/?message_type=3", status_code=303)

# Маршрут для DELETE запроса на страницу с чатами (для удаления чата)
@app.delete("/chats/{chatName}", response_class=RedirectResponse)
def delete_chat(request: Request, chatName: str, db: Session = Depends(get_db), current_user: Users = Depends(get_current_user)):
    # Получаем из БД запись с чатом, который нужно удалить
    chat = db.query(Chats).filter(Chats.name == chatName).first()

    # Ошибка поиска чата в БД
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Удаляем чат из запись о чате
    db.delete(chat)
    db.commit()
    
    return RedirectResponse(url="/chats/", status_code=303)

# Маршрут для создания токена для пользователя и чата
@app.post("/get_token_for_chat/", response_model=Token)
async def get_token_for_chat(chat_request: ChatRequest, current_user: Users = Depends(get_current_user), db: Session = Depends(get_db)):
    # Проверка того, что токен создается для существующей комнаты
    chat = db.query(Chats).filter(Chats.name == chat_request.chat_name).first()
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Генерация JWT токена для пользователя и чата
    token = generate_token_for_chat(current_user.email, chat_request.chat_name)
    return {"access_token": token, "token_type": "bearer"}

# Маршрут для страницы поиска чатов по названию
@app.get("/search/", response_class=HTMLResponse)
def search_chats(request: Request, query: str, db: Session = Depends(get_db), current_user: Users = Depends(get_current_user)):
    # Проверка того, что длина названия чата не менее 6 символов
    if (len(query) < 6):
        return templates.TemplateResponse("search_results.html", {"request": request, "query": query, "message": "Длина названия комнаты должна быть не менее 6 символов"})

    # Выполняем запрос в базу данных, фильтруем по частичному совпадению названия чата
    chats = db.query(Chats).filter(Chats.name.ilike(f"%{query}%")).all()
    
    return templates.TemplateResponse("search_results.html", {"request": request, "chats": chats, "query": query})

# Маршрут для отображения страницы с чатами
@app.get("/meeting_room/", response_class=HTMLResponse)
def meeting_room(request: Request, db: Session = Depends(get_db), current_user: Users = Depends(get_current_user)):
    return templates.TemplateResponse("meeting_room.html", {"request": request})

# Маршрут для выхода из аккаунта
@app.get("/logout/", response_model=LogoutMessage)
async def logout(request: Request, response: Response):
    # Очищаем сессию
    request.session.clear()   
    return {"message": "Был произведен выход из аккаунта"}

# Основная страница, позволяет зарегестрироваться, либо авторизоваться
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, is_authorizate: bool = Depends(is_user_authorizate)):
    if (is_authorizate):
        return templates.TemplateResponse("main_page.html", {"request": request, "button_message": "Перейти к чатам", "authorizate": "yes"})
    return templates.TemplateResponse("main_page.html", {"request": request, "button_message": "Авторизоваться"})