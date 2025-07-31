from flask import Blueprint, request, jsonify
from firebase_utils import firestore
from encryption_utils import encrypt_data
import uuid

merchant_bp = Blueprint('merchant', __name__)

@merchant_bp.route('/merchant/transaction', methods=['POST'])
def merchant_add_transaction():
    """
    json expected:
    {
        "userId": "user_id",
        "accountId": "account_id",
        "amount": 100.0,
        "category": "Food",
        "merchant": "KFC",
        }

    """
    data = request.json
    user_id = data['userId']
    account_id = data['accountId']
    transaction_id = str(uuid.uuid4())

    encrypted_tx = {
        'amount': data['amount'],
        'category': encrypt_data(data['category']),
        'merchant': encrypt_data(data['merchant']),
        'status': "success",
        'timestamp': firestore.SERVER_TIMESTAMP
    }

    tx_ref = firestore.collection('users')\
        .document(user_id).collection('linkedAccounts')\
        .document(account_id).collection('transactions')\
        .document(transaction_id)

    tx_ref.set(encrypted_tx)
    return jsonify({'transactionId': transaction_id}), 200
