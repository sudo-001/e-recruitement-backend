import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', "postgresql://postgres:postgres@localhost:5432/erecruitment")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', "JwtSecretKey")
    
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI='sqlite:///:memory'
    JWT_SECRET_KEY="testsecretkey"