from fastapi import APIRouter, Request, Query, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from dependencies import get_db, get_current_user, HTMLResponse, RedirectResponse
from models import Icon, Saint, Tradition

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
