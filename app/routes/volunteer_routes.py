from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from datetime import datetime
from app import mongo
from app.utils.auth_helpers import token_required

volunteer_bp = Blueprint('volunteer_bp', __name__)

@volunteer_bp.route("/volunteer/available", methods=["GET"])
@token_required
def get_available_donations(current_user):
    db = mongo.db
    if current_user['role'] != 'volunteer':
        return jsonify({"error": "Only volunteers can view this"}), 403

    donations = list(db.donations.find({"status": "pending", "volunteerId": None}))
    for d in donations:
        d['_id'] = str(d['_id'])
        d['donorId'] = str(d['donorId'])
    return jsonify(donations)

@volunteer_bp.route("/volunteer/assign/<donation_id>", methods=["POST"])
@token_required
def assign_donation(current_user, donation_id):
    db = mongo.db
    if current_user['role'] != 'volunteer':
        return jsonify({"error": "Only volunteers can accept assignments"}), 403

    donation = db.donations.find_one({"_id": ObjectId(donation_id)})
    if not donation:
        return jsonify({"error": "Donation not found"}), 404
    if donation.get("volunteerId"):
        return jsonify({"error": "Already assigned to another volunteer"}), 400

    db.donations.update_one(
        {"_id": ObjectId(donation_id)},
        {"$set": {"volunteerId": current_user['_id']}}
    )
    return jsonify({"message": "You have been assigned to the donation"})
@volunteer_bp.route("/volunteer/my-assignments", methods=["GET"])
@token_required
def get_my_assignments(current_user):
    db = mongo.db
    if current_user['role'] != 'volunteer':
        return jsonify({"error": "Only volunteers can view their assignments"}), 403

    donations = list(db.donations.find({ "volunteerId": current_user['_id'] }))
    for d in donations:
        d['_id'] = str(d['_id'])
        d['donorId'] = str(d['donorId'])
        d['volunteerId'] = str(d['volunteerId'])
    return jsonify(donations)
