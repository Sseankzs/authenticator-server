from flask import Blueprint, request, jsonify
from firebase_utils import db, firestore
from encryption_utils import encrypt_data, decrypt_vector
import uuid
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        "transactionId": "optional_custom_id",
        "amount": 100.0,
        "category": "Food",
        "merchant": "KFC",
        "vector": [0.1, 0.2, ..., 0.3]  ← live scanned palm vector
    }
    """
    data = request.json
    input_vector = data.get('vector')
    if not input_vector:
        return jsonify({'error': 'Palm vector is required'}), 400

    # Step 1: Find matching user
    users_ref = db.collection("users").stream()
    matched_user_id = None
    logger.info("Starting palm vector matching process...")
    
    for user in users_ref:
        user_data = user.to_dict()
        if "palmVector" not in user_data:
            continue
        try:
            stored_vector = decrypt_vector(user_data["palmVector"])
            similarity = cosine_similarity(input_vector, stored_vector)
            logger.info(f"User {user.id}: similarity = {similarity:.4f}")
            if similarity >= 0.99:
                matched_user_id = user.id
                logger.info(f"✓ Match found! User ID: {matched_user_id} (similarity: {similarity:.4f})")
                break
        except Exception as e:
            logger.warning(f"Error processing user {user.id}: {str(e)}")
            continue

    if not matched_user_id:
        logger.error("No matching user found with similarity >= 0.95")
        return jsonify({'error': 'No matching user found'}), 403

    # Step 2: Get default account
    matched_user_doc = db.collection("users").document(matched_user_id).get()
    default_account = matched_user_doc.to_dict().get("defaultAccount")
    if not default_account:
        return jsonify({'error': 'Default account not set'}), 400

    # Step 3: Store transaction
    transaction_id = str(uuid.uuid4())
    encrypted_tx = {
        'transactionId': data.get('transactionId', transaction_id),
        'amount': data['amount'],
        'category': encrypt_data(data['category']),
        'merchant': encrypt_data(data['merchant']),
        'status': "success",
        'timestamp': firestore.SERVER_TIMESTAMP
    }

    tx_ref = db.collection('users') \
        .document(matched_user_id) \
        .collection('linkedAccounts') \
        .document(default_account) \
        .collection('transactions') \
        .document(transaction_id)

    tx_ref.set(encrypted_tx)
    return jsonify({'transactionId': transaction_id}), 200
