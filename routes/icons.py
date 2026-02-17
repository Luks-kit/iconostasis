from fastapi import APIRouter, Request, Depends, Form, Query, File, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
import cloudinary
import cloudinary.uploader
from sqlalchemy.orm import Session
from dependencies import get_db, get_current_user, HTMLResponse
from models import Icon, Saint, Tradition, User, Comment


templates = Jinja2Templates(directory="templates")
router = APIRouter()


# Display details for a specific icon
@router.get("/icon/{icon_id}", response_class=HTMLResponse)
def icon_detail(request: Request, icon_id: int, db: Session = Depends(get_db)):
    icon = db.query(Icon).filter(Icon.id == icon_id).first()
    if not icon:
        return HTMLResponse(content="Icon not found", status_code=404)
    
    user = get_current_user(request, db)
    return templates.TemplateResponse("icon.html", {
        "request": request,
        "user": user,
        "icon": icon,
        "uploader_name": db.query(User).filter(User.id == icon.user_id).first().display_name    
    })

# FastAPI JSON endpoint for bot
@router.get("/api/icon/{icon_id}")
def icon_api(icon_id: int, db: Session = Depends(get_db)):
    icon = db.query(Icon).filter(Icon.id == icon_id).first()
    if not icon:
        return {"error": "Not found"}, 404
    
    return {
        "title": icon.title,
        "saints": [s.name for s in icon.saints],
        "tradition": icon.tradition.name,
        "century": icon.century,
        "region": icon.region,
        "iconographer": icon.iconographer or "Unknown",
        "uploader": db.query(User).filter(User.id == icon.user_id).first().display_name,
        "image_url": icon.image_url,
        "description": icon.description
    }



@router.get("/icon/{icon_id}/image")
def serve_icon_image(icon_id: int, db: Session = Depends(get_db)):
    icon = db.query(Icon).filter(Icon.id == icon_id).first()
    if not icon:
        return JSONResponse({"error": "Icon not found"}, status_code=404)
    
    return RedirectResponse(url=icon.image_url)

@router.post("/icon/{icon_id}/delete")
def delete_icon(
    icon_id: int, 
    db: Session = Depends(get_db), 
    request: Request = None # Needed to get session user
    ):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401)

    icon = db.query(Icon).filter(Icon.id == icon_id).first()
    
    if not icon:
        raise HTTPException(status_code=404)

    # Permission Check: Only owner or admin
    if icon.user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(icon)
    db.commit()
    return {"status": "success"}

@router.get("/icon/{icon_id}/edit", response_class=HTMLResponse)
def edit_icon_form(request: Request, icon_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    icon = db.query(Icon).filter(Icon.id == icon_id).first()
    if not icon:
        return HTMLResponse(content="Icon not found", status_code=404)

    # Permission Check: Only owner or admin
    if icon.user_id != user.id and not user.is_admin:
        return HTMLResponse(content="Not authorized", status_code=403)

    traditions = db.query(Tradition).all()
    return templates.TemplateResponse("edit_icon.html", {
        "request": request,
        "user": user,
        "icon": icon,
        "traditions": traditions
    })
    
@router.post("/icon/{icon_id}/comment")
async def add_comment(
    icon_id: int, 
    request: Request, 
    text: str = Form(...), 
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    new_comment = Comment(
        text=text.strip(),
        user_id=user.id,
        icon_id=icon_id
    )
    
    db.add(new_comment)
    db.commit()
    
    # Redirect back to the icon page to see the new comment
    return RedirectResponse(url=f"/icon/{icon_id}", status_code=303)

@router.post("/icon/{icon_id}/venerate")
async def toggle_veneration(icon_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"error": "Login required"}, status_code=401)

    icon = db.query(Icon).filter(Icon.id == icon_id).first()
    if not icon:
        return JSONResponse({"error": "Icon not found"}, status_code=404)

    if user in icon.venerators:
        icon.venerators.remove(user)
        action = "unlit"
    else:
        icon.venerators.append(user)
        action = "lit"

    db.commit()
    return {"action": action, "count": len(icon.venerators)}

@router.post("/icon/{icon_id}/edit", response_class=HTMLResponse)
def edit_icon(
    request: Request,
    icon_id: int,
    db: Session = Depends(get_db),
    title: str = Form(...),
    century: str = Form(None),
    region: str = Form(None),
    iconographer: str = Form(None),
    description: str = Form(None),
    saints: str = Form(None),  # Comma-separated saint names
    tradition_id: int = Form(...)
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    icon = db.query(Icon).filter(Icon.id == icon_id).first()
    if not icon:
        return HTMLResponse(content="Icon not found", status_code=404)

    # Permission Check: Only owner or admin
    if icon.user_id != user.id and not user.is_admin:
        return HTMLResponse(content="Not authorized", status_code=403)

    icon.title = title
    icon.century = century
    icon.region = region
    icon.iconographer = iconographer
    icon.description = description
    icon.tradition_id = tradition_id

    if saints is not None:
        saint_names = [s.strip() for s in saints.split(",")]
        new_saints = []
        for name in saint_names:
            saint = db.query(Saint).filter(Saint.name == name).first()
            if not saint:
                saint = Saint(name=name)
                db.add(saint)
                db.commit()
            new_saints.append(saint)
        icon.saints = new_saints

    db.commit()
    
    return RedirectResponse(url=f"/icon/{icon_id}", status_code=303)


#Render the icon upload form
@router.get("/upload", response_class=HTMLResponse)
def upload_form(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    traditions = db.query(Tradition).all()
    return templates.TemplateResponse("upload.html", {
        "request": request,
        "user": user,
        "traditions": traditions
    })


#Handle icon upload form submission
@router.post("/upload", response_class=HTMLResponse)
def upload_icon(
    request: Request,
    db: Session = Depends(get_db),
    title: str = Form(...),
    century: str = Form(None),
    region: str = Form(None),
    iconographer: str = Form(None),
    description: str = Form(None),
    saints: str = Form(None),  # Comma-separated saint names
    tradition_id: int = Form(...),
    image_file: UploadFile = File(...)
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    image_file.file.seek(0)
    upload_result = cloudinary.uploader.upload(image_file.file)
    image_url = upload_result["secure_url"]
    
    # Create new icon
    new_icon = Icon(
        title=title,
        image_url=image_url,
        century=century,
        region=region,
        iconographer=iconographer,
        description=description,
        tradition_id=tradition_id,
        user_id=user.id
    )
    
    if saints:
        saint_names = [s.strip() for s in saints.split(",")]
        for name in saint_names:
            saint = db.query(Saint).filter(Saint.name == name).first()
            if not saint:
                saint = Saint(name=name)
                db.add(saint)
                db.commit()
            new_icon.saints.append(saint)

    db.add(new_icon)
    db.commit()
    
    return templates.TemplateResponse("upload_success.html", {
        "request": request,
        "user": user,
        "icon": new_icon
    })
