import cloudinary
from config import CLOUD_NAME, CLOUD_KEY, CLOUD_SECRET, CLOUDINARY_URL

cloudinary.config(
    cloud_name=CLOUD_NAME,
    api_key=CLOUD_KEY,
    api_secret=CLOUD_SECRET,
    cloudinary_url=CLOUDINARY_URL
)
