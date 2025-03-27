from flask import Flask
from flask_pymongo import PyMongo
from flask_cors import CORS
from dotenv import load_dotenv
import os

mongo = PyMongo()

def create_app():
    load_dotenv()

    app = Flask(__name__)
    CORS(app)

    app.config['MONGO_URI'] ="mongodb+srv://lahiruflutter:lahiru@cluster0.oxqke.mongodb.net/foodapp?retryWrites=true&w=majority&appName=Cluster0"
    app.config['SECRET_KEY'] ="mysupersecret"

    mongo.init_app(app)

    # Import and register Blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.donation_routes import donation_bp
    from app.routes.volunteer_routes import volunteer_bp
    
    app.register_blueprint(volunteer_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(donation_bp)

    return app
