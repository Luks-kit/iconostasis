from fastapi import APIRouter, Request, Form, status, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import bcrypt
from dependencies import get_db, get_current_user
from models import ModRank, User
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

DEFAULT_MOD_RANK_NAME = "Catechumen"


#Render the login form
@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

#Handle login form submission
@router.post("/login")
def login_user(request: Request, db: Session = Depends(get_db), username: str = Form(...), password: str = Form(...)):
    user = db.query(User).filter(User.username == username).first()
    
    if not user or not bcrypt.checkpw(password.encode("utf-8"), user.hashed_pw.encode("utf-8")):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"}, status_code=401)

    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=status.HTTP_302_FOUND)


#Render the signup form
@router.get("/signup")
def signup_form(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


#Handle signup form submission
@router.post("/signup")
def signup_user(request: Request, db: Session = Depends(get_db), username: str = Form(...), displayname: str = Form(...), email: str = Form(...), password: str = Form(...)):
    import re
    if not re.fullmatch("^[a-zA-Z0-9_]*$", username):
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Username must be alphanumeric"})

    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Username already taken"}, status_code=409)

    default_rank = db.query(ModRank).filter(ModRank.name == DEFAULT_MOD_RANK_NAME).first()
    if not default_rank:
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "Signup is temporarily unavailable. Please try again shortly."},
            status_code=503,
        )

    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    new_user = User(
        username=username,
        display_name=displayname,
        email=email,
        hashed_pw=hashed_pw,
        mod_rank_id=default_rank.id,
    )
    db.add(new_user)
    db.commit()
    return RedirectResponse("/login", status_code=302)

#Handle logout
@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)
