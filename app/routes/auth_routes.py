from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import jwt
import datetime
from app import mongo

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    db = mongo.db
    data = request.json
    if db.users.find_one({"email": data["email"]}):
        return jsonify({"error": "User already exists"}), 400

    hashed_pw = generate_password_hash(data["password"])
    user = {
        "name": data["name"],
        "email": data["email"],
        "password": hashed_pw,
        "role": data["role"],
        "location": data.get("location", {}),
        "createdAt": datetime.datetime.utcnow()
    }
    db.users.insert_one(user)
    return jsonify({"message": "User registered successfully"}), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    db = mongo.db
    data = request.json
    user = db.users.find_one({"email": data["email"]})
    if not user or not check_password_hash(user['password'], data['password']):
        return jsonify({"error": "Invalid credentials"}), 401

    token = jwt.encode({
        "id": str(user['_id']),
        "role": user['role'],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }, current_app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({"token": token})
