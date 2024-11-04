from fastapi import FastAPI, Request, Form, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from database import engine, Base, get_db, Users, Chats, create_new_user
from schema import UserRegister, UserAuthorizate, Token, ChatRequest, LogoutMessage
from exceptions import verify_password, is_valid_email, are_fields_filled, is_user_exist, generate_token_for_chat
from auth import create_access_token, get_current_user, is_user_authorizate
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

# Создание таблиц в базе данных
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Добавление поддержки сессий для авторизации
app.add_middleware(SessionMiddleware, secret_key="your_secret_key")

templates = Jinja2Templates(directory="templates")

# Вспомогательные функции для преобразования данных форм в модели

async def getUserRegister(email: str = Form(None), password: str = Form(None)) -> UserRegister:
    """Преобразует данные из формы регистрации в модель UserRegister."""
    return UserRegister(email=email, password=password)

async def getUserAuthorizate(email: str = Form(None), password: str = Form(None)) -> UserAuthorizate:
    """Преобразует данные из формы авторизации в модель UserAuthorizate."""
    return UserAuthorizate(email=email, password=password)

# Маршруты приложения
@app.api_route("/register/", methods=["GET", "POST"], response_class=HTMLResponse)
async def register(request: Request, db: Session = Depends(get_db), user: UserRegister = Depends(getUserRegister)):
    if request.method == "POST":
        if not is_valid_email(user.email):
            return templates.TemplateResponse("register.html", {"request": request, "message_bad": "Email введен некорректно"})

        if not are_fields_filled(user):
            return templates.TemplateResponse("register.html", {"request": request, "message": "Ошибка ввода"})

        if is_user_exist(db, user.email):
            return templates.TemplateResponse("register.html", {"request": request, "message_bad": "Аккаунт с таким email уже существует"})

        create_new_user(db, user.email, user.password)
        return templates.TemplateResponse("register.html", {"request": request, "message_good": "Аккаунт успешно зарегистрирован"})

    return templates.TemplateResponse("register.html", {"request": request})

@app.api_route("/authorizate/", methods=["GET", "POST"], response_class=HTMLResponse)
async def authorizate(request: Request, response: Response, db: Session = Depends(get_db), form_data: UserAuthorizate = Depends(getUserAuthorizate), is_authorizate: bool = Depends(is_user_authorizate)):
    """Маршрут для авторизации (GET и POST-запросы)."""

    # Обработка GET-запроса
    if request.method == "GET":
        if is_authorizate:
            return RedirectResponse(url="/chats/")
        return templates.TemplateResponse("authorizate.html", {"request": request})

    # Обработка POST-запроса
    elif request.method == "POST":
        user = db.query(Users).filter(Users.email == form_data.email).first()
        if not user or not verify_password(form_data.password, user.password):
            return templates.TemplateResponse("authorizate.html", {"request": request, "message_no": "Неверные данные"})

        access_token = create_access_token(data={"email": user.email})
        request.session['token'] = access_token
        return templates.TemplateResponse("authorizate.html", {"request": request, "message_yes": "Успешный вход", "token": access_token})


@app.api_route("/chats/", methods=["GET", "POST"], response_class=HTMLResponse)
async def chats(request: Request, db: Session = Depends(get_db), current_user: Users = Depends(get_current_user), name: str = Form(None), message_type: str = None):
    """Обработка страницы с чатами для GET и POST запросов."""

    # Словарь сообщений
    messages = {
        "1": "Длина названия чата должна быть более 6 символов",
        "2": "Чат уже существует",
        "3": "Чат успешно создан"
    }

    # Обработка POST-запроса (создание чата)
    if request.method == "POST":
        if len(name) < 6:
            return RedirectResponse(url="/chats/?message_type=1", status_code=303)

        if db.query(Chats).filter(Chats.name == name).first():
            return RedirectResponse(url="/chats/?message_type=2", status_code=303)

        # Создание нового чата
        new_chat = Chats(id=db.query(Chats).count(), name=name, owner=current_user.email)
        db.add(new_chat)
        db.commit()
        db.refresh(new_chat)
        return RedirectResponse(url="/chats/?message_type=3", status_code=303)

    # Обработка GET-запроса (отображение списка чатов)
    chats = db.query(Chats).filter(Chats.owner == current_user.email).all()
    message = messages.get(message_type)
    return templates.TemplateResponse("chats.html", {"request": request, "chats": chats, "message": message})


@app.delete("/chats/{chatName}", response_class=RedirectResponse)
def delete_chat(chatName: str, db: Session = Depends(get_db), current_user: Users = Depends(get_current_user)):
    """Удаление чата пользователя по его названию."""
    chat = db.query(Chats).filter(Chats.name == chatName).first()
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")

    db.delete(chat)
    db.commit()
    return RedirectResponse(url="/chats/", status_code=303)

@app.post("/get_token_for_chat/", response_model=Token)
async def get_token_for_chat(chat_request: ChatRequest, current_user: Users = Depends(get_current_user), db: Session = Depends(get_db)):
    """Создание токена для чата при существующем пользователе и комнате."""
    chat = db.query(Chats).filter(Chats.name == chat_request.chat_name).first()
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")

    token = generate_token_for_chat(current_user.email, chat_request.chat_name)
    return {"access_token": token, "token_type": "bearer"}

@app.get("/search/", response_class=HTMLResponse)
def search_chats(request: Request, query: str, db: Session = Depends(get_db), current_user: Users = Depends(get_current_user)):
    """Поиск чатов по названию."""
    if len(query) < 6:
        return templates.TemplateResponse("search_results.html", {"request": request, "query": query, "message": "Длина названия комнаты должна быть не менее 6 символов"})

    chats = db.query(Chats).filter(Chats.name.ilike(f"%{query}%")).all()
    return templates.TemplateResponse("search_results.html", {"request": request, "chats": chats, "query": query})

@app.get("/meeting_room/", response_class=HTMLResponse)
def meeting_room(request: Request, db: Session = Depends(get_db), current_user: Users = Depends(get_current_user)):
    """Отображение страницы 'Комната встречи'."""
    return templates.TemplateResponse("meeting_room.html", {"request": request})

@app.get("/logout/", response_model=LogoutMessage)
async def logout(request: Request, response: Response):
    """Выход из аккаунта и очистка сессии."""
    request.session.clear()
    return {"message": "Выход из аккаунта"}

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, is_authorizate: bool = Depends(is_user_authorizate)):
    """Главная страница с переходом к авторизации или чатам."""
    button_message = "Перейти к чатам" if is_authorizate else "Авторизоваться"
    return templates.TemplateResponse("main_page.html", {"request": request, "button_message": button_message})
