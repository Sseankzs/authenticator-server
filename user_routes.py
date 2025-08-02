# user_routes.py
import datetime
from flask import Blueprint, request, jsonify
from firebase_utils import db
from encryption_utils import encrypt_data, decrypt_data, tokenize_vector

user_bp = Blueprint('user', __name__)

# Register user
@user_bp.route("/register_user", methods=["POST"])
def register_user():
    data = request.json
    user_id = data["userId"]
    encrypted_data = {
        "email": encrypt_data(data["email"]),
        "fullName": encrypt_data(data["fullName"]),
        "icNumber": encrypt_data(data["icNumber"]),
        "phoneNumber": encrypt_data(data.get("phoneNumber", "")),
        "defaultAccount": "",
        "preferences": {},
    }
    db.collection("users").document(user_id).set(encrypted_data)
    return jsonify({"message": "User registered"}), 200

@user_bp.route("/update_user_profile", methods=["POST"])
def update_user_profile():
    """
    JSON expected:
    {
        "userId": "user_id",
        "email": "new_email",              # optional
        "fullName": "new_name",            # optional
        "icNumber": "new_ic",              # optional
        "phoneNumber": "new_phone_number"  # optional
    }
    """
    data = request.json
    user_id = data.get("userId")
    if not user_id:
        return jsonify({"error": "Missing userId"}), 400

    update_fields = {}
    if "email" in data:
        update_fields["email"] = encrypt_data(data["email"])
    if "fullName" in data:
        update_fields["fullName"] = encrypt_data(data["fullName"])
    if "icNumber" in data:
        update_fields["icNumber"] = encrypt_data(data["icNumber"])
    if "phoneNumber" in data:
        update_fields["phoneNumber"] = encrypt_data(data["phoneNumber"])

    if not update_fields:
        return jsonify({"message": "No fields to update"}), 400

    db.collection("users").document(user_id).update(update_fields)
    return jsonify({"message": "User profile updated"}), 200

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
    tokenized_vector = tokenize_vector(data["vector"])
    db.collection("users").document(user_id).set({"palmToken": tokenized_vector}, merge=True)
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


# Get all user info
@user_bp.route("/get_user_info/<user_id>", methods=["GET"])
def get_user_info(user_id):
    user_doc = db.collection("users").document(user_id).get()
    if not user_doc.exists:
        return jsonify({"error": "User not found"}), 404

    user_data = user_doc.to_dict()
    decrypted_info = {
        "email": decrypt_data(user_data.get("email", "")),
        "fullName": decrypt_data(user_data.get("fullName", "")),
        "icNumber": decrypt_data(user_data.get("icNumber", "")),
        "phoneNumber": decrypt_data(user_data.get("phoneNumber", "")),
        "defaultAccount": user_data.get("defaultAccount", ""),
        "preferences": user_data.get("preferences", {}),
    }

    # Get bank accounts
    accounts_ref = db.collection("users").document(user_id).collection("linkedAccounts").stream()
    accounts = []
    for acc in accounts_ref:
        acc_data = acc.to_dict()
        accounts.append({
            "bankAccountId": acc.id,
            "bankName": decrypt_data(acc_data.get("bankName", "")),
            "accountType": decrypt_data(acc_data.get("accountType", "")),
            "balance": acc_data.get("balance", 0),
        })

    # Get all transactions
    transactions = []
    for acc in accounts:
        acc_id = acc["bankAccountId"].lower()
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

    # Dashboard data (last month only, by category)
    now = datetime.datetime.utcnow()
    one_month_ago = now - datetime.timedelta(days=30)
    category_totals = {}
    for txn in transactions:
        if txn["timestamp"].replace(tzinfo=None) >= one_month_ago:
            cat = txn["category"]
            category_totals[cat] = category_totals.get(cat, 0) + txn["amount"]

    return jsonify({
        "profile": decrypted_info,
        "linkedAccounts": accounts,
        "transactions": transactions,
        "dashboard": category_totals
    }), 200
