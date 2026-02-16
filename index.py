import os
import cloudinary
import cloudinary_config
import database
import dependencies
from fastapi import FastAPI, Request, Depends, Query, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker
from models import Base, Icon, ModRank, Saint, Tradition, User
from routes import users, icons, home, auth


app = FastAPI()
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


DEFAULT_MOD_RANKS = [
    {
        "name": "User",
        "description": "Can candle, but all other actions need moderation approval.",
        "requires_moderation": True,
        "can_moderate": False,
        "can_lock_conversations": False,
        "is_admin": False,
    },
    {
        "name": "Trusted User",
        "description": "Can perform actions without moderation approval.",
        "requires_moderation": False,
        "can_moderate": False,
        "can_lock_conversations": False,
        "is_admin": False,
    },
    {
        "name": "Moderator",
        "description": "Can approve or deny posts and lock conversations.",
        "requires_moderation": False,
        "can_moderate": True,
        "can_lock_conversations": True,
        "is_admin": False,
    },
    {
        "name": "Admin",
        "description": "Administrative account with direct database access.",
        "requires_moderation": False,
        "can_moderate": True,
        "can_lock_conversations": True,
        "is_admin": True,
    },
]


def add_mod_rank_column_if_missing() -> None:
    inspector = inspect(database.engine)
    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "mod_rank_id" in user_columns:
        return

    dialect = database.engine.dialect.name
    with database.engine.begin() as connection:
        if dialect == "postgresql":
            connection.execute(text("ALTER TABLE users ADD COLUMN mod_rank_id INTEGER"))
        elif dialect == "sqlite":
            connection.execute(text("ALTER TABLE users ADD COLUMN mod_rank_id INTEGER"))
        else:
            connection.execute(text("ALTER TABLE users ADD COLUMN mod_rank_id INTEGER"))


def assign_default_rank_to_existing_users() -> None:
    with database.SessionLocal() as db:
        default_rank = db.query(ModRank).filter(ModRank.name == "User").first()
        if not default_rank:
            return
        db.query(User).filter(User.mod_rank_id.is_(None)).update(
            {User.mod_rank_id: default_rank.id},
            synchronize_session=False,
        )
        db.commit()


def seed_mod_ranks() -> None:
    with database.SessionLocal() as db:
        existing_ranks = {rank.name for rank in db.query(ModRank).all()}
        for rank_data in DEFAULT_MOD_RANKS:
            if rank_data["name"] in existing_ranks:
                continue
            db.add(ModRank(**rank_data))
        db.commit()


@app.on_event("startup")
def initialize_database() -> None:
    Base.metadata.create_all(bind=database.engine)
    add_mod_rank_column_if_missing()
    seed_mod_ranks()
    assign_default_rank_to_existing_users()

@app.api_route("/health", methods=["GET", "HEAD"])
def health_check():
        return {"status": "ok"}
