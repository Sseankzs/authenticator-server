from flask import Blueprint, request, jsonify
from firebase_utils import db, firestore
from encryption_utils import encrypt_data, resolve_vector_token
import uuid
import numpy as np
import logging
import ast

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

merchant_bp = Blueprint('merchant', __name__)

def cosine_similarity(vec1, vec2):
    try:
        vec1 = ast.literal_eval(vec1) if isinstance(vec1, str) else vec1
        vec2 = ast.literal_eval(vec2) if isinstance(vec2, str) else vec2
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    except Exception:
        return -1  # so it will never match

@merchant_bp.route('/merchant/add_transaction', methods=['POST'])
def merchant_add_transaction():
    """
    json expected:
    {
        "mode": "palm" or "face" # yet to be implemented
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

    logger.info(f"Starting palm vector matching process...")
    logger.info(f"Input vector length: {len(input_vector)}")

    # Step 1: Match against vectors in tokenVault
    vault_docs = db.collection("tokenVault").stream()
    matched_token_id = None
    best_similarity = -1

    for doc in vault_docs:
        vault_data = doc.to_dict()
        mode = data.get("mode", "palm")  # default to palm
        vector_key = "palmVector" if mode == "palm" else "faceVector"
        stored_vector = vault_data.get(vector_key)

        
        if not stored_vector:
            logger.info(f"Token {doc.id}: No vector found, skipping")
            continue
            
        try:
            similarity = cosine_similarity(input_vector, stored_vector)
            logger.info(f"Token {doc.id}: similarity = {similarity:.4f}")
            
            if similarity >= 0.99 and similarity > best_similarity:
                best_similarity = similarity
                matched_token_id = doc.id
                logger.info(f"✓ New best match! Token ID: {matched_token_id} (similarity: {similarity:.4f})")
                
        except Exception as e:
            logger.warning(f"Error comparing token {doc.id}: {str(e)}")
            continue

    if not matched_token_id:
        logger.error("No matching token found with similarity >= 0.99")
        return jsonify({'error': 'No matching palm vector found'}), 403

    logger.info(f"Best match: Token {matched_token_id} with similarity {best_similarity:.4f}")

    # Step 2: Find user who has this token
    logger.info(f"Searching for user with palmToken: {matched_token_id}")
    users_docs = db.collection("users").stream()
    matched_user_id = None

    for user_doc in users_docs:
        user_data = user_doc.to_dict()
        user_palm_token = user_data.get("palmToken")
        
        if user_palm_token == matched_token_id:
            matched_user_id = user_doc.id
            logger.info(f"✓ Found user with matching token! User ID: {matched_user_id}")
            break

    if not matched_user_id:
        logger.error(f"No user found with palmToken: {matched_token_id}")
        return jsonify({'error': 'User not found for matching palm vector'}), 403

    # Step 3: Get default account
    category = data['category']
    matched_user_doc = db.collection("users").document(matched_user_id).get()
    user_data = matched_user_doc.to_dict()
    preferences = user_data.get("preferences", {})
    preferred_account = preferences.get(category)
    
    if not preferred_account:
        logger.info(f"No preferred account found for category '{category}', using defaultAccount.")
        preferred_account = user_data.get("defaultAccount")
        
    if not preferred_account:
        logger.error(f"No suitable account found for user {matched_user_id}")
        return jsonify({'error': 'No suitable account found'}), 400

    logger.info(f"Using account: {preferred_account} for user {matched_user_id}")

    # Step 4: Store transaction
    transaction_id = data.get('transactionId', str(uuid.uuid4()))
    encrypted_tx = {
        'transactionId': transaction_id,
        'amount': data['amount'],
        'category': data['category'],
        'merchant': data['merchant'],
        'status': "success",
        'timestamp': firestore.SERVER_TIMESTAMP
    }

    tx_ref = db.collection('users') \
        .document(matched_user_id) \
        .collection('linkedAccounts') \
        .document(preferred_account) \
        .collection('transactions') \
        .document(transaction_id)

    logger.info(f"📁 Storing transaction at: users/{matched_user_id}/linkedAccounts/{preferred_account}/transactions/{transaction_id}")
    logger.info(f"💰 Transaction: {data['merchant']} - ${data['amount']} ({data['category']})")
    
    tx_ref.set(encrypted_tx)
    logger.info(f"✅ Transaction {transaction_id} successfully stored!")
    
    return jsonify({
        'transactionId': transaction_id,
        'userId': matched_user_id,
        'similarity': best_similarity
    }), 200