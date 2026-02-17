from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from dependencies import get_db, get_current_user, Session
from models import User, Icon

templates = Jinja2Templates(directory="templates")
router = APIRouter()

# Display user profile with their uploaded icons
@router.get("/user/{username}", response_class=HTMLResponse)
def user_profile(request: Request, username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return HTMLResponse(content="User not found", status_code=404)
    
    venerated_icons = db.query(Icon).filter(Icon.venerators.any(id=user.id)).all()
    icons = db.query(Icon).filter(Icon.user_id == user.id).all()
    current_user = get_current_user(request, db)
    
    
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": current_user,
        "profile_user": user,
        "icons": icons,
        "venerated_icons": venerated_icons
    })
    
#Settings page for each user
@router.get("/settings", response_class=HTMLResponse)
def user_settings(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return HTMLResponse(content="Unauthorized", status_code=401)
    
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "user": user,
        "icons": db.query(Icon).filter(Icon.user_id == user.id).all() # Show user's icons in settings
    })
    
@router.post("/settings/edit/display_name", response_class=HTMLResponse)
def edit_display_name(request: Request, db: Session = Depends(get_db), new_display_name: str = Form(...)):
    user = get_current_user(request, db)
    if not user:
        return HTMLResponse(content="Unauthorized", status_code=401)
    
    user.display_name = new_display_name
    db.commit()
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "user": user,
        "message": "Display name updated successfully"
    })
    
