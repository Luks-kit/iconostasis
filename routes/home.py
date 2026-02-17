from fastapi import APIRouter, Request, Query, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from dependencies import get_db, get_current_user, HTMLResponse, RedirectResponse
from models import Icon, Saint, Tradition, User, Comment

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Home page with optional filters for saint, tradition, century, and region
@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db), saint: str = Query(None), tradition_id: int = Query(0), century: str = Query(None), region: str = Query(None)):
    query = db.query(Icon)
    user = get_current_user(request, db)

    if tradition_id > 0:
        query = query.filter(Icon.tradition_id == tradition_id)
    if saint:
        query = query.join(Icon.saints).filter(Saint.name.ilike(f"%{saint}%"))
    if century:
        query = query.filter(Icon.century.ilike(f"%{century}%"))
    if region:
        query = query.filter(Icon.region.ilike(f"%{region}%"))

    icons = query.all()
    traditions = db.query(Tradition).all()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user,
        "icons": icons,
        "traditions": traditions,
        "selected_tradition": str(tradition_id),
        "saint": saint or "",
        "century": century or "",
        "region": region or ""
    })

@router.post("/comment/{comment_id}/delete")
def delete_comment(
    comment_id: int, 
    request: Request, 
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401)

    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Save the icon_id before we delete the comment so we can redirect back
    target_icon_id = comment.icon_id

    if comment.user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(comment)
    db.commit()
    
    return RedirectResponse(url=f"/icon/{target_icon_id}", status_code=303)