from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Config
app.config['MONGO_URI'] = os.getenv("MONGO_URI")
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

mongo = PyMongo(app)
db = mongo.db

# Test DB Connection
try:
    db.command("ping")
    print("✅ MongoDB connected successfully!")
except Exception as e:
    print("❌ MongoDB connection failed:", str(e))

# Utils
def token_required(f):
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Missing token"}), 401
        try:
            token = token.split(" ")[1]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = db.users.find_one({"_id": ObjectId(data['id'])})
        except Exception as e:
            return jsonify({"error": "Invalid token"}), 401
        return f(current_user, *args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

# Routes

@app.route("/register", methods=["POST"])
def register():
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

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = db.users.find_one({"email": data["email"]})
    if not user or not check_password_hash(user['password'], data['password']):
        return jsonify({"error": "Invalid credentials"}), 401
    token = jwt.encode({
        "id": str(user['_id']),
        "role": user['role'],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    return jsonify({"token": token})

@app.route("/donate", methods=["POST"])
@token_required
def create_donation(current_user):
    if current_user['role'] != 'donor':
        return jsonify({"error": "Only donors can post donations"}), 403
    data = request.json
    donation = {
        "donorId": current_user['_id'],
        "foodName": data['foodName'],
        "quantity": data['quantity'],
        "pickupLocation": data['pickupLocation'],
        "expiresAt": datetime.datetime.strptime(data['expiresAt'], "%Y-%m-%dT%H:%M"),
        "status": "pending",
        "claimedBy": None,
        "volunteerId": None,
        "confirmed": False,
        "createdAt": datetime.datetime.utcnow()
    }
    db.donations.insert_one(donation)
    return jsonify({"message": "Donation created"})

@app.route("/donations", methods=["GET"])
@token_required
def get_donations(current_user):
    donations = list(db.donations.find({"status": "pending"}))
    for d in donations:
        d['_id'] = str(d['_id'])
        d['donorId'] = str(d['donorId'])
    return jsonify(donations)

@app.route("/confirm/<donation_id>", methods=["POST"])
@token_required
def confirm_donation(current_user, donation_id):
    donation = db.donations.find_one({"_id": ObjectId(donation_id)})
    if not donation:
        return jsonify({"error": "Donation not found"}), 404
    if current_user['role'] != 'receiver':
        return jsonify({"error": "Only receivers can confirm donations"}), 403
    db.donations.update_one({"_id": ObjectId(donation_id)}, {"$set": {"status": "completed", "confirmed": True, "claimedBy": current_user['_id']}})
    return jsonify({"message": "Donation confirmed"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
