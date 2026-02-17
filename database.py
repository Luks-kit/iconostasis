from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={}, 
    pool_pre_ping=True, 
    pool_size=10, 
    max_overflow=20,
    pool_timeout=30
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
