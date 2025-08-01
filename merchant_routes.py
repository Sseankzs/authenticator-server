from flask import Blueprint, request, jsonify
from firebase_utils import db, firestore
from encryption_utils import encrypt_data, decrypt_vector
import uuid
import numpy as np

merchant_bp = Blueprint('merchant', __name__)

def cosine_similarity(vec1, vec2):
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

@merchant_bp.route('/merchant/add_transaction', methods=['POST'])
def merchant_add_transaction():
    """
    json expected:
    {
        "userId": "user_id",
        "accountId": "account_id",
        "transactionId": "transaction_id", (optional)
        "amount": 100.0,
        "category": "Food",
        "merchant": "KFC",
        "vector": [0.1, 0.2, ..., 0.3]  ← live scanned palm vector
    }
    """
    data = request.json
    user_id = data['userId']
    account_id = data['accountId']
    transaction_id = data.get('transactionId', str(uuid.uuid4()))
    input_vector = data.get('vector')

    if not input_vector:
        return jsonify({'error': 'Palm vector is required'}), 400

    # Step 1: Get user's stored encrypted palm vector
    user_doc = db.collection("users").document(user_id).get()
    if not user_doc.exists:
        return jsonify({'error': 'User not found'}), 404

    user_data = user_doc.to_dict()
    if "palmVector" not in user_data:
        return jsonify({'error': 'No palm vector stored for user'}), 400

    stored_vector = decrypt_vector(user_data["palmVector"])
    similarity = cosine_similarity(input_vector, stored_vector)

    if similarity < 0.95:  # Set your threshold
        return jsonify({'error': 'Palm verification failed'}), 403

    # Step 2: Encrypt and store the transaction
    encrypted_tx = {
        'amount': data['amount'],
        'category': encrypt_data(data['category']),
        'merchant': encrypt_data(data['merchant']),
        'status': "success",
        'timestamp': firestore.SERVER_TIMESTAMP
    }

    tx_ref = db.collection('users')\
        .document(user_id).collection('linkedAccounts')\
        .document(account_id).collection('transactions')\
        .document(transaction_id)

    tx_ref.set(encrypted_tx)
    return jsonify({'transactionId': transaction_id}), 200
