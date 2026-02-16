import os

SECRET_KEY = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

CLOUD_NAME = os.getenv("CLOUD_NAME")
CLOUD_KEY = os.getenv("CLOUD_KEY")
CLOUD_SECRET = os.getenv("CLOUD_SECRET")
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL")
