from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
import os
from flask_cors import CORS

from .config import Config, TestingConfig 

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_name=None):
    app = Flask(__name__)

   
    if config_name == "testing":
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(Config)
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', "postgresql://postgres:postgres@localhost:5432/erecruitment")
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', "JwtSecretKey")
    
        
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Enable CORS for all routes
    CORS(app, resources={r"/*": {"origins": "*"}})

    from .routes import main
    app.register_blueprint(main)

    return app
