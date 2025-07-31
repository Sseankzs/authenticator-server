# merchant_routes.py

from flask import Blueprint, request, jsonify
from firebase_admin import firestore
from datetime import datetime

bp = Blueprint("merchant", __name__)
db = firestore.client()

@bp.route("/merchant/add_transaction", methods=["POST"])
def merchant_add_transaction():
    data = request.json
    required = ["userId", "accountId", "transactionId", "amount", "category", "merchant", "status"]

    if not all(k in data for k in required):
        return jsonify({"error": "Missing fields"}), 400

    trx_ref = db.collection("users").document(data["userId"]) \
                .collection("bankAccounts").document(data["accountId"]) \
                .collection("transactions").document(data["transactionId"])

    trx_ref.set({
        "amount": data["amount"],
        "category": data["category"],
        "merchant": data["merchant"],
        "status": data["status"],
        "timestamp": data.get("timestamp", datetime.utcnow())
    })

    return jsonify({"status": "Transaction added by merchant"}), 200
