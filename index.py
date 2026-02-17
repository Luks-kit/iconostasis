import os
import cloudinary
import cloudinary_config
import database
import dependencies
import iconobot
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, Query, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker
from models import Base, Icon, ModRank, Saint, Tradition, User
from routes import users, icons, home, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(iconobot.bot.start(os.getenv("DISCORD_BOT_TOKEN")))
    
    yield
    
    # Shutdown logic:
    await iconobot.bot.close()
    task.cancel()

app = FastAPI(lifespan=lifespan)
app.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv("SECRET_KEY")
)

templates = Jinja2Templates(directory="templates")

app.include_router(users.router)
app.include_router(icons.router)
app.include_router(home.router)
app.include_router(auth.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
def start_bot() -> None:
    iconobot.bot.run(os.getenv("DISCORD_BOT_TOKEN"))

@app.api_route("/health", methods=["GET", "HEAD"])
def health_check():
        return {"status": "ok"}
