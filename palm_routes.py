# palm_routes.py

from flask import Blueprint, request, jsonify
from firebase_admin import firestore

bp = Blueprint("palm", __name__)
db = firestore.client()

@bp.route("/register_palm", methods=["POST"])
def register_palm():
    data = request.json
    required = ["userId", "vector"]

    if not all(k in data for k in required):
        return jsonify({"error": "Missing fields"}), 400

    db.collection("palmVectors").document(data["userId"]).set({
        "vector": data["vector"]
    })

    return jsonify({"status": "Palm vector registered"}), 200
