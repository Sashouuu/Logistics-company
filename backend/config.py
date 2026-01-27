import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://{user}:{pwd}@{host}:{port}/{db}?charset=utf8mb4"
    ).format(
        user=os.getenv("DB_USER", "root"),
        pwd=os.getenv("DB_PASSWORD", "admin$123"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "3306"),
        db=os.getenv("DB_NAME", "logistics_company"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me")
