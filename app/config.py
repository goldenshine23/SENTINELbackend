import os
from dotenv import load_dotenv
load_dotenv()

META_API_TOKEN = os.getenv("META_API_TOKEN")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

DATABASE_URL = "sqlite:///./users.db"
