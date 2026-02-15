import os
import cloudinary
import cloudinary.uploader
import bcrypt
from fastapi import FastAPI, Request, Query, Form, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from models import Base, Icon, Saint, Tradition, User


app = FastAPI()
app.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv("SECRET_KEY")
)

templates = Jinja2Templates(directory="templates")


# Serve the 'static' folder at /static
app.mount("/static", StaticFiles(directory="static"), name="static")


# SQLite/PostgreSQL connection
# Note: Neon requires SSL, so we ensure the URL ends with ?sslmode=require
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, connect_args={}, pool_pre_ping=True, pool_size=1, max_overflow=0)
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

def get_current_user(request: Request, db: Session):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == int(user_id)).first()


# Home page
@app.get("/", response_class=HTMLResponse)
def home(
    request: Request, 
    db: Session =  Depends(get_db),
    saint: str = Query(None),
    tradition_id: int = Query(0),
    century: str = Query(None),
    region: str = Query(None)
):
    query = db.query(Icon)
    user = get_current_user(request, db)

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
        "user": user,
        "icons": icons,
        "traditions": traditions,
        "selected_tradition": str(tradition_id),
        "saint": saint or "",
        "century": century or "",
        "region": region or ""
    })

# Icon detail page
@app.get("/icon/{icon_id}", response_class=HTMLResponse)
def icon_detail(request: Request, icon_id: int, db: Session = Depends(get_db)):
    icon = db.query(Icon).filter(Icon.id == icon_id).first()
    if not icon:
        return HTMLResponse(content="Icon not found", status_code=404)
    
    uploader_name = db.query(Users).filter(User.id == icon.user_id).first().display_name
    return templates.TemplateResponse("icon.html", {"request": request, "icon": icon, "user": get_current_user(request, db), "uploader_name": uploader_name})


@app.get("/upload", response_class=HTMLResponse)
def upload_form(request: Request, db: Session =  Depends(get_db)):
    traditions = db.query(Tradition).all()
    return templates.TemplateResponse("upload.html", {"request": request, "traditions": traditions, "user": get_current_user(request, db)})

@app.post("/upload", response_class=HTMLResponse)
def upload_icon(
    request: Request,
    db: Session =  Depends(get_db),
    title: str = Form(...),
    century: str = Form(None),
    region: str = Form(None),
    iconographer: str = Form(None),
    description: str = Form(None),
    tradition_id: int = Form(...),
    saints: str = Form(None),
    image_file: UploadFile = File(...)
):
    image_file.file.seek(0)
    
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

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
        image_url=optimized_url,
        user_id=user.id
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

    return templates.TemplateResponse("upload_success.html", {"request": request, "icon": icon, "user": user})

@app.get("/login", response_class=HTMLResponse)
def log_in_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request })

@app.post("/login", response_class=HTMLResponse)
def log_in( 
    request: Request,
    db: Session =  Depends(get_db),
    username: str = Form(...), 
    password: str = Form(...)
):
    
    # 1. Look for the user
    user = db.query(User).filter(User.username == username).first()
    
    # 2. Verify password using bcrypt directly
    if not user:
        return templates.TemplateResponse(name="login.html", context={
            "request": request,
            "error": "No user with that username found"
        }, status_code=401)
    # bcrypt needs bytes, so we encode the strings
    is_valid: bool = bcrypt.checkpw(
        password.encode('utf-8'), 
        user.hashed_pw.encode('utf-8')
    )

    if not is_valid:
        return templates.TemplateResponse(name="login.html", context={
            "request": request, 
            "error": "Invalid password"
        }, status_code=401)

    # 3. Success
    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@app.get("/signup", response_class=HTMLResponse)
def signup_form(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.post("/signup")
def signup_user(
    request: Request,
    db: Session =  Depends(get_db),
    username: str = Form(...),
    displayname: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):

    import re.fullmatch
    if not fullmatch("^[a-zA-Z0-0_]*$", username):
        return templates.TemplateResponse("signup.html", {"error": "Username must be alphanumeric"})
        
    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse("signup.html", {
            "request": request, 
            "error": "Username already taken"
        }, status_code=409)


    # 1. Hash the password
    # gensalt() generates a random salt and handles the complexity for you
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)

    # 2. Create the User object
    # We .decode('utf-8') the hash to store it as a string in Postgres
    new_user = User(
        username=username,
        display_name=displayname,
        email=email,
        hashed_pw=hashed_password.decode('utf-8')
    )
    

    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/login", status_code=302)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)

@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}

"""

@app.get("/user/{username}", response_class=HTMLResponse)
def public_profile(username: str, request: Request, db: Session = Depends(get_db)):
    # Look up by the unique username string
    target_user = db.query(User).filter(User.username == username).first()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Get all icons uploaded by this specific user
    user_icons = db.query(Icon).filter(Icon.user_id == target_user.id).all()
    
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "profile_user": target_user,
        "icons": user_icons,
        "user": get_current_user(request, db) # The person currently browsing
    })

"""
