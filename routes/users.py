from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from dependencies import get_db, get_current_user, Session
from models import User, Icon

templates = Jinja2Templates(directory="templates")
router = APIRouter()

@router.get("/user/{username}", response_class=HTMLResponse)
def user_profile(request: Request, username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return HTMLResponse(content="User not found", status_code=404)
    
    icons = db.query(Icon).filter(Icon.user_id == user.id).all()
    current_user = get_current_user(request, db)
    
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": current_user,
        "profile_user": user,
        "icons": icons
    })
    
