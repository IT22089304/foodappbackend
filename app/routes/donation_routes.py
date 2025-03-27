from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from datetime import datetime
from app import mongo
from app.utils.auth_helpers import token_required

donation_bp = Blueprint('donation_bp', __name__)

@donation_bp.route("/donate", methods=["POST"])
@token_required
def create_donation(current_user):
    db = mongo.db
    if current_user['role'] != 'donor':
        return jsonify({"error": "Only donors can post donations"}), 403

    data = request.json
    donation = {
        "donorId": current_user['_id'],
        "foodName": data['foodName'],
        "quantity": data['quantity'],
        "pickupLocation": data['pickupLocation'],
        "expiresAt": datetime.strptime(data['expiresAt'], "%Y-%m-%dT%H:%M"),
        "status": "pending",
        "claimedBy": None,
        "volunteerId": None,
        "confirmed": False,
        "createdAt": datetime.utcnow()
    }
    db.donations.insert_one(donation)
    return jsonify({"message": "Donation created"})

@donation_bp.route("/donations", methods=["GET"])
@token_required
def get_donations(current_user):
    db = mongo.db
    donations = list(db.donations.find({"status": "pending"}))
    for d in donations:
        d['_id'] = str(d['_id'])
        d['donorId'] = str(d['donorId'])
    return jsonify(donations)

@donation_bp.route("/confirm/<donation_id>", methods=["POST"])
@token_required
def confirm_donation(current_user, donation_id):
    db = mongo.db
    donation = db.donations.find_one({"_id": ObjectId(donation_id)})
    if not donation:
        return jsonify({"error": "Donation not found"}), 404
    if current_user['role'] != 'receiver':
        return jsonify({"error": "Only receivers can confirm donations"}), 403

    db.donations.update_one(
        {"_id": ObjectId(donation_id)},
        {"$set": {
            "status": "completed",
            "confirmed": True,
            "claimedBy": current_user['_id']
        }}
    )
    return jsonify({"message": "Donation confirmed"})
