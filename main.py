import os
import cloudinary
import cloudinary.uploader
from passlib.hash import bcyrpt
from fastapi import FastAPI, Request, Query, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Icon, Saint, Tradition


app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Serve the 'static' folder at /static
app.mount("/static", StaticFiles(directory="static"), name="static")


# SQLite/PostgreSQL connection
# Note: Neon requires SSL, so we ensure the URL ends with ?sslmode=require
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Conditional connect_args
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# 2. Cloudinary Configuration
cloudinary.config(
    cloud_name = os.getenv("CLOUD_NAME"),
    api_key = os.getenv("CLOUD_KEY"),
    api_secret = os.getenv("CLOUD_SECRET"),
    cloudinary_url = os.getenv("CLOUDINARY_URL")
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Home page
@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    saint: str = Query(None),
    tradition_id: int = Query(0),
    century: str = Query(None),
    region: str = Query(None)
):
    db = SessionLocal()
    query = db.query(Icon)

    # Filter by tradition
    if tradition_id > 0:
        query = query.filter(Icon.tradition_id == tradition_id)

    # Filter by saint
    if saint:
        query = query.join(Icon.saints).filter(Saint.name.ilike(f"%{saint}%"))

    # Filter by century
    if century:
        query = query.filter(Icon.century.ilike(f"%{century}%"))

    # Filter by region
    if region:
        query = query.filter(Icon.region.ilike(f"%{region}%"))

    icons = query.all()
    traditions = db.query(Tradition).all()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "icons": icons,
        "traditions": traditions,
        "selected_tradition": str(tradition_id),
        "saint": saint or "",
        "century": century or "",
        "region": region or ""
    })

# Icon detail page
@app.get("/icon/{icon_id}", response_class=HTMLResponse)
def icon_detail(request: Request, icon_id: int):
    db = SessionLocal()
    icon = db.query(Icon).filter(Icon.id == icon_id).first()
    if not icon:
        return HTMLResponse(content="Icon not found", status_code=404)
    return templates.TemplateResponse("icon.html", {"request": request, "icon": icon})

@app.get("/upload", response_class=HTMLResponse)
def upload_form(request: Request):
    db = SessionLocal()
    traditions = db.query(Tradition).all()
    return templates.TemplateResponse("upload.html", {"request": request, "traditions": traditions})

@app.post("/upload", response_class=HTMLResponse)
def upload_icon(
    request: Request,
    title: str = Form(...),
    century: str = Form(None),
    region: str = Form(None),
    iconographer: str = Form(None),
    description: str = Form(None),
    tradition_id: int = Form(...),
    saints: str = Form(None),
    image_file: UploadFile = File(...)
):
    db = SessionLocal()
    image_file.file.seek(0)

    upload_result = cloudinary.uploader.upload(image_file.file)
    optimized_url = upload_result["secure_url"]

    # Create new Icon
    icon = Icon(
        title=title,
        century=century,
        region=region,
        iconographer=iconographer,
        description=description,
        tradition_id=tradition_id,
        image_url=optimized_url
    )

    # Handle saints
    if saints:
        saint_names = [s.strip() for s in saints.split(",")]
        for name in saint_names:
            saint = db.query(Saint).filter(Saint.name == name).first()
            if not saint:
                saint = Saint(name=name)
                db.add(saint)
                db.commit()
            icon.saints.append(saint)

    db.add(icon)
    db.commit()

    return templates.TemplateResponse("upload_success.html", {"request": request, "icon": icon})

@app.get("/login", response_class=HTMLResponse)
def log_in_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request })

@app.post("/login", response_class=HTMLResponse)
def log_in( 
    request: Request
    username: str = Form(...), 
    password: str = Form(...)
):
    db = SessionLocal()
    
    # 1. Look for the user in the database
    user = db.query(User).filter(User.username == username).first()
    
    # 2. Check if user exists AND if the password is correct
    # pwd_context.verify takes (plain_text_password, hashed_password_from_db)
    if not user or not pwd_context.verify(password, user.password_hash):
        # If it fails, send them back to login with an error message
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "Invalid username or password"
        })

    # 3. If successful, redirect to home or dashboard
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    # TODO: Set a cookie or JWT token here so the browser "remembers" them
    # response.set_cookie(key="session_id", value="xyz123") 
    
    return response
    

