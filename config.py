import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Config:
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "todo_app")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey123")
