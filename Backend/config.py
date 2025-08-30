import os
from dotenv import load_dotenv

load_dotenv()

# Class-based access
class Settings:
    META_API_TOKEN = os.getenv("META_API_TOKEN")

# Instance of Settings class
settings = Settings()

# Direct variable access (optional but available if needed)
META_API_TOKEN = settings.META_API_TOKEN
