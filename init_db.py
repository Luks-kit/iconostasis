from sqlalchemy import create_engine
from models import Base

engine = create_engine("sqlite:///database.db")

# Create tables
Base.metadata.create_all(bind=engine)

print("Database created successfully!")

