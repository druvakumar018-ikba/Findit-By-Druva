import os
import secrets
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

IS_SERVERLESS = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
IS_PRODUCTION = IS_SERVERLESS or os.getenv("APP_ENV", "").lower() == "production" or os.getenv("FLASK_ENV", "").lower() == "production"
TEMP_DIR = tempfile.gettempdir()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or (None if IS_PRODUCTION else secrets.token_urlsafe(48))
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or (None if IS_PRODUCTION else secrets.token_urlsafe(48))
    JWT_ACCESS_TOKEN_EXPIRES_DAYS = 7
    # Upload settings (in serverless/Vercel, filesystem is read-only except tempdir)
    if IS_SERVERLESS:
        UPLOAD_FOLDER = os.path.join(TEMP_DIR, "findit_uploads")
    else:
        UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))  # 5 MB

    # Cloudinary config (used for persistent image uploads in production)
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")

    # Database Settings (MySQL / local dev fallback)
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "findit_db")

    MYSQL_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    if IS_SERVERLESS:
        SQLITE_URI = f"sqlite:///{os.path.join(TEMP_DIR, 'findit.db')}"
    else:
        SQLITE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'findit.db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @classmethod
    def get_database_uri(cls):
        # 1. Explicit DATABASE_URL takes top priority (Supabase, Neon, PostgreSQL, or Cloud MySQL)
        custom_url = os.getenv("DATABASE_URL", "").strip()
        if custom_url:
            # SQLAlchemy requires 'postgresql://' instead of deprecated 'postgres://'
            if custom_url.startswith("postgres://"):
                custom_url = custom_url.replace("postgres://", "postgresql://", 1)
            if IS_SERVERLESS and custom_url.startswith("sqlite:"):
                raise RuntimeError("Serverless deployments require a persistent DATABASE_URL.")
            return custom_url

        # 2. Serverless instances cannot safely share a local SQLite database.
        if IS_SERVERLESS:
            raise RuntimeError("DATABASE_URL must point to a persistent database in serverless deployments.")

        # 3. Try local MySQL
        try:
            import pymysql
            conn = pymysql.connect(
                host=cls.DB_HOST,
                port=int(cls.DB_PORT),
                user=cls.DB_USER,
                password=cls.DB_PASSWORD,
                connect_timeout=2
            )
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{cls.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            conn.commit()
            conn.close()
            print(f"[FindIt Backend] Successfully connected to MySQL at {cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}")
            return cls.MYSQL_URI
        except Exception as e:
            if IS_PRODUCTION:
                raise RuntimeError("Production database is unavailable; configure a persistent database.") from e
            print(f"[FindIt Backend] MySQL connection not active ({e}). Defaulting to SQLite database at {cls.SQLITE_URI} for smooth development & testing.")
            return cls.SQLITE_URI
