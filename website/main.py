from fastapi import FastAPI, Request, Form, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from database import engine, Base, get_db, Users, Chats, reset_id_sequence
from schema import UserAuthorization, Token, ChatRequest, LogoutMessage
from exceptions import verify_password, is_valid_email, is_user_exist, generate_token_for_chat, create_new_user
from auth import generate_access_token, get_current_user, is_user_authenticated
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse, JSONResponse

# Создание таблиц в базе данных
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Добавление поддержки сессий для авторизации
app.add_middleware(SessionMiddleware, secret_key="your_secret_key")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.api_route("/registration/", methods=["GET", "POST"], response_class=HTMLResponse)
async def registration(request: Request, db: Session = Depends(get_db), email: str = Form(None), password: str = Form(None)):

    if request.method == "POST":
        # Проверка корректности email
        if not is_valid_email(email):
            return templates.TemplateResponse(
                "registration.html",
                {"request": request, "message_bad": "Email введен некорректно"}
            )

        # Проверка заполненности полей
        if not email or not password:
            return templates.TemplateResponse(
                "registration.html",
                {"request": request, "message": "Ошибка ввода"}
            )

        # Проверка существования пользователя
        if is_user_exist(db, email):
            return templates.TemplateResponse(
                "registration.html",
                {"request": request, "message_bad": "Аккаунт с таким email уже существует"}
            )

        # Создание нового пользователя
        create_new_user(db, email, password)

        # Генерация JWT токена
        access_token = generate_access_token(data={"email": email})

        # Сохранение токена в сессии
        request.session['token'] = access_token

        # Перенаправление на защищенную страницу (например, список чатов)
        return RedirectResponse(url="/chats/", status_code=303)

    # Обработка GET-запроса для отображения страницы регистрации
    return templates.TemplateResponse("registration.html", {"request": request})


@app.api_route("/authorization/", methods=["GET", "POST"], response_class=HTMLResponse)
async def authorization(request: Request, db: Session = Depends(get_db), email: str = Form(None), password: str = Form(None), is_authorizate: bool = Depends(is_user_authenticated)):

    # Обработка GET-запроса
    if request.method == "GET":
        if is_authorizate:
            return RedirectResponse(url="/chats/")
        return templates.TemplateResponse("authorization.html", {"request": request})

    # Обработка POST-запроса
    elif request.method == "POST":
        form_data = UserAuthorization(email=email, password=password)
        user = db.query(Users).filter(Users.email == form_data.email).first()
        if not user or not verify_password(form_data.password, user.password):
            return templates.TemplateResponse("authorization.html", {"request": request, "message_no": "Неверные данные"}, status_code=401)

        access_token = generate_access_token(data={"email": user.email})
        request.session['token'] = access_token
        return templates.TemplateResponse("authorization.html", {"request": request, "message_yes": "Успешный вход", "token": access_token})


@app.api_route("/chats/", methods=["GET", "POST"], response_class=HTMLResponse)
async def chats(request: Request, db: Session = Depends(get_db), current_user: Users = Depends(get_current_user), name: str = Form(None), message_type: str = None):

    # Словарь сообщений
    messages = {
        "1": "Длина названия чата должна быть более 6 символов",
        "2": "Чат уже существует",
        "3": "Чат создан"
    }

    # Обработка POST-запроса (создание чата)
    if request.method == "POST":
        if len(name) < 6:
            return RedirectResponse(url="/chats/?message_type=1", status_code=303)

        if db.query(Chats).filter(Chats.name == name).first():
            return RedirectResponse(url="/chats/?message_type=2", status_code=303)

        # Создание нового чата
        reset_id_sequence(db, 'chats')
        new_chat = Chats(name=name, owner=current_user.email)
        db.add(new_chat)
        db.commit()
        db.refresh(new_chat)
        return RedirectResponse(url="/chats/?message_type=3", status_code=303)

    # Обработка GET-запроса (отображение списка чатов)
    chats = db.query(Chats).filter(Chats.owner == current_user.email).all()
    message = messages.get(message_type)
    return templates.TemplateResponse("main.html", {"request": request, "chats": chats, "message": message, "message_type": message_type})

# Удаление чата пользователя по его названию
@app.delete("/chats/{chatName}", response_class=RedirectResponse)
def delete_chat(chatName: str, db: Session = Depends(get_db)):

    chat = db.query(Chats).filter(Chats.name == chatName).first()
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")

    db.delete(chat)
    db.commit()
    return RedirectResponse(url="/chats/", status_code=303)

# Создание токена для чата при существующем пользователе и комнате
@app.post("/get_token_for_chat/", response_model=Token)
async def get_token_for_chat(chat_request: ChatRequest, current_user: Users = Depends(get_current_user), db: Session = Depends(get_db)):

    chat = db.query(Chats).filter(Chats.name == chat_request.chat_name).first()
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")

    token = generate_token_for_chat(current_user.email, chat_request.chat_name)
    return {"access_token": token, "token_type": "bearer"}

# Поиск чатов по названию
@app.get("/search/", response_class=JSONResponse)
async def search_chats(query: str = Query(...), db: Session = Depends(get_db)):

    if len(query) < 6:
        return JSONResponse(content={"chats": [], "message": "Длина названия комнаты должна быть не менее 6 символов"})

    chats = db.query(Chats).filter(Chats.name.ilike(f"%{query}%")).all()
    chat_list = [{"name": chat.name} for chat in chats]
    return JSONResponse(content={"chats": chat_list})

# Отображение страницы чата
@app.get("/chat/", response_class=HTMLResponse)
def chat(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

# Выход из аккаунта и очистка сессии
@app.get("/logout/", response_model=LogoutMessage)
async def logout(request: Request):
    request.session.clear()
    return {"message": "Выход из аккаунта"}

# Приветственная страница
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, is_authorizate: bool = Depends(is_user_authenticated)):
    button_message = "Перейти к чатам" if is_authorizate else "Авторизоваться"
    return templates.TemplateResponse("welcome.html", {"request": request, "button_message": button_message})
