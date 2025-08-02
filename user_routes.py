# user_routes.py
import datetime
from flask import Blueprint, request, jsonify
from firebase_utils import db
from encryption_utils import encrypt_data, decrypt_data, encrypt_vector, decrypt_vector
from token_utils import tokenize_value, resolve_token

user_bp = Blueprint('user', __name__)

# Register user
@user_bp.route("/register_user", methods=["POST"])
def register_user():
    data = request.json
    user_id = data["userId"]
    encrypted_data = {
        "email": tokenize_value(data["email"]),
        "fullName": tokenize_value(data["fullName"]),
        "icNumber": tokenize_value(data["icNumber"]),
        "phoneNumber": tokenize_value(data.get("phoneNumber", "")),
        "defaultAccount": "",
        "preferences": {},
    }
    db.collection("users").document(user_id).set(encrypted_data)
    return jsonify({"message": "User registered"}), 200

# Register palm vector (encrypted)
@user_bp.route("/register_palm", methods=["POST"])
def register_palm():
    """
    JSON expected:
    {
        "userId": "user_id",
        "vector": [1, 2, 3]
    }
    """
    data = request.json
    #check if valid json passed
    if "userId" not in data or "vector" not in data:
        return jsonify({"error": "Missing userId or vector"}), 400
    if not isinstance(data["vector"], list):
        return jsonify({"error": "Vector must be a list"}), 400
    
    user_id = data["userId"]
    tokenized_vector = tokenize_value(data["vector"])
    db.collection("users").document(user_id).update({"palmToken": tokenized_vector})
    return jsonify({"message": "Palm registered"}), 200

# Add bank account
@user_bp.route("/add_bank_account", methods=["POST"])
def add_account():
    data = request.json
    acc_id = data["bankAccountId"]
    account_data = {
        "bankName": encrypt_data(data["bankName"]),
        "accountType": encrypt_data(data["accountType"]),
        "balance": data["balance"],
    }
    db.collection("users").document(data["userId"]).collection("linkedAccounts").document(acc_id).set(account_data)
    return jsonify({"message": "Bank account added"}), 200

# Set default account
@user_bp.route("/set_default_account", methods=["POST"])
def set_default_account():
    data = request.json
    user_id = data["userId"]
    default_acc = data["accountId"]
    db.collection("users").document(user_id).update({"defaultAccount": default_acc})
    return jsonify({"message": "Default account set"}), 200

# Update preferences (future use)
@user_bp.route("/user/<user_id>/set_preferences", methods=["POST"])
def set_preferences(user_id):
    prefs = request.json.get("preferences", {})
    db.collection("users").document(user_id).update({"preferences": prefs})
    return jsonify({"message": "Preferences updated"}), 200

# Get user transactions
@user_bp.route("/transactions/<user_id>", methods=["GET"])
def get_transactions(user_id):
    """
    JSON expected:
    {
        "userId": "uZsYmasM5B3dVXTYjt3J"
    }
    """
    user_doc = db.collection("users").document(user_id).get()
    if not user_doc.exists:
        return jsonify({"error": "User not found"}), 404

    transactions = []
    accounts_ref = db.collection("users").document(user_id).collection("linkedAccounts").stream()
    for acc in accounts_ref:
        acc_id = acc.id
        txns = db.collection("users").document(user_id).collection("linkedAccounts") \
            .document(acc_id).collection("transactions").stream()
        for txn in txns:
            txn_data = txn.to_dict()
            transactions.append({
                "transactionId": txn.id,
                "amount": txn_data["amount"],
                "category": decrypt_data(txn_data["category"]),
                "merchant": decrypt_data(txn_data["merchant"]),
                "status": txn_data["status"],
                "timestamp": txn_data["timestamp"],
                "bankAccountId": acc_id
            })

    return jsonify({"transactions": transactions}), 200
