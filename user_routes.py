# user_routes.py

from flask import Blueprint, request, jsonify
from firebase_admin import firestore

bp = Blueprint("user", __name__)
db = firestore.client()

@bp.route("/register", methods=["POST"])
def register_user():
    data = request.json
    required = ["userId", "email", "fullName", "icNumber", "phoneNumber"]

    if not all(k in data for k in required):
        return jsonify({"error": "Missing fields"}), 400

    user_ref = db.collection("users").document(data["userId"])
    user_ref.set({
        "email": data["email"],
        "fullName": data["fullName"],
        "icNumber": data["icNumber"],
        "phoneNumber": data["phoneNumber"],
        "defaultAccount": None
    }, merge=True)

    return jsonify({"status": "User registered"}), 200

@bp.route("/user/<user_id>", methods=["GET"])
def get_user_info(user_id):
    doc = db.collection("users").document(user_id).get()
    if not doc.exists:
        return jsonify({"error": "User not found"}), 404

    user_data = doc.to_dict()

    # Fetch bank accounts
    accounts = db.collection("users").document(user_id).collection("bankAccounts").stream()
    bank_accounts = {}
    for acc in accounts:
        acc_data = acc.to_dict()
        trx_stream = db.collection("users").document(user_id) \
                        .collection("bankAccounts").document(acc.id) \
                        .collection("transactions").stream()
        transactions = [t.to_dict() for t in trx_stream]
        acc_data["transactions"] = transactions
        bank_accounts[acc.id] = acc_data

    user_data["bankAccounts"] = bank_accounts
    return jsonify(user_data), 200

@bp.route("/user/<user_id>/add_account", methods=["POST"])
def add_bank_account(user_id):
    data = request.json
    required = ["bankAccountId", "bankName", "accountType", "balance"]

    if not all(k in data for k in required):
        return jsonify({"error": "Missing fields"}), 400

    acc_ref = db.collection("users").document(user_id).collection("bankAccounts").document(data["bankAccountId"])
    acc_ref.set({
        "bankName": data["bankName"],
        "accountType": data["accountType"],
        "balance": data["balance"]
    })

    return jsonify({"status": "Bank account added"}), 200

@bp.route("/user/<user_id>/set_default_account", methods=["POST"])
def set_default_account(user_id):
    data = request.json
    default_id = data.get("defaultAccount")

    if not default_id:
        return jsonify({"error": "Missing defaultAccount"}), 400

    db.collection("users").document(user_id).update({
        "defaultAccount": default_id
    })

    return jsonify({"status": "Default account set"}), 200