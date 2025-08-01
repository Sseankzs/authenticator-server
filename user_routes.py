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
    data = request.json
    if "userId" not in data or "vector" not in data:
        return jsonify({"error": "Missing userId or vector"}), 400
    if not isinstance(data["vector"], list):
        return jsonify({"error": "Vector must be a list"}), 400
    user_id = data["userId"]
    encrypted_vector = encrypt_vector(data["vector"])
    db.collection("users").document(user_id).update({"palmVector": encrypted_vector})
    return jsonify({"message": "Palm vector registered"}), 200

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
    db.collection("users").document(user_id).update({"accountId": default_acc})
    db.collection("users").document(user_id).update({"defaultAccount": data["bankName"] + "_" + data["accountType"] })
    return jsonify({"message": "Default account set"}), 200

# Update preferences (future use)
@user_bp.route("/user/<user_id>/set_preferences", methods=["POST"])
def set_preferences(user_id):
    prefs = request.json.get("preferences", {})
    db.collection("users").document(user_id).update({"preferences": prefs})
    return jsonify({"message": "Preferences updated"}), 200

# Get all user info
@user_bp.route("/get_user_info/<user_id>", methods=["GET"])
def get_user_info(user_id):
    user_doc = db.collection("users").document(user_id).get()
    if not user_doc.exists:
        return jsonify({"error": "User not found"}), 404

    user_data = user_doc.to_dict()
    decrypted_info = {
        "email": resolve_token(user_data.get("email", "")),
        "fullName": resolve_token(user_data.get("fullName", "")),
        "icNumber": resolve_token(user_data.get("icNumber", "")),
        "phoneNumber": resolve_token(user_data.get("phoneNumber", "")),
        "defaultAccount": user_data.get("defaultAccount", ""),
        "preferences": user_data.get("preferences", {}),
    }

    # Get bank accounts
    accounts_ref = db.collection("users").document(user_id).collection("bankAccounts").stream()
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
        acc_id = acc["bankAccountId"]
        txns = db.collection("users").document(user_id).collection("bankAccounts") \
            .document(acc_id).collection("transactions").stream()
        for txn in txns:
            txn_data = txn.to_dict()
            transactions.append({
                "transactionId": txn.id,
                "amount": txn_data["amount"],
                "category": txn_data["category"],
                "merchant": txn_data["merchant"],
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
        "bankAccounts": accounts,
        "transactions": transactions,
        "dashboard": category_totals
    }), 200

@user_bp.route("/transactions/<user_id>", methods=["GET"])
def get_transactions(user_id):
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

@user_bp.route("/dashboard/<user_id>", methods=["GET"])
def get_dashboard(user_id):
    now = datetime.datetime.now()
    month_start = datetime.datetime(now.year, now.month, 1)

    user_ref = db.collection('users').document(user_id)
    banks_ref = user_ref.collection('bankAccounts')

    banks = banks_ref.stream()
    all_transactions = []

    for bank in banks:
        txns_ref = banks_ref.document(bank.id).collection('transactions')
        txns = txns_ref.where('timestamp', '>=', month_start).order_by('timestamp').stream()
        for txn in txns:
            data = txn.to_dict()
            amount = float(data['amount']) if isinstance(data['amount'], (int, float)) else float(str(data['amount']))
            all_transactions.append({
                'amount': amount,
                'category': data.get('category', 'Others'),
                'timestamp': data.get('timestamp'),
                'merchant': data.get('merchant', ''),
                'status': data.get('status', '')
            })

    total_spent = sum(txn['amount'] for txn in all_transactions)
    category_totals = {}
    for txn in all_transactions:
        cat = txn['category']
        category_totals[cat] = category_totals.get(cat, 0) + txn['amount']

    return {
        'totalSpent': total_spent,
        'categoryTotals': category_totals,
        'transactionCount': len(all_transactions)
    }
