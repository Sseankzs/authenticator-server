from flask import Blueprint, request, jsonify
from firebase_admin import firestore
from uuid import uuid4
from encryption_utils import encrypt_vector, decrypt_vector 
from numpy import dot
from numpy.linalg import norm

db = firestore.client()
palm_bp = Blueprint('palm', __name__)

@palm_bp.route("/register_palm", methods=["POST"])
def register_palm():
    """
    json expected:
    {
        "user_id": "user_id",
        "vector": [1, 2, 3]
    }
    """

    try:
        data = request.json
        user_id = data.get("user_id")
        feature_vector = data.get("vector")

        if not user_id or not feature_vector:
            return jsonify({"error": "Missing user_id or vector"}), 400

        # Generate unique palm token
        token_id = str(uuid4())

        # Encrypt the vector
        encrypted_vector = encrypt_vector(feature_vector)

        # Store the encrypted vector in tokenVault
        db.collection("tokenVault").document(token_id).set({
            "encryptedVector": encrypted_vector,
            "createdAt": firestore.SERVER_TIMESTAMP
        })

        # Link token to user document
        db.collection("users").document(user_id).update({
            "palmToken": token_id
        })

        return jsonify({"message": "Palm registered successfully", "token": token_id}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@palm_bp.route("/verify_vector", methods=["POST"])
def verify_vector():
    """
    Input JSON:
    {
        "vector": [0.1, 0.2, ...]  # The biometric vector
    }

    Returns:
    {
        "userId": "user_123"
    } or 401 if not matched
    """
    data = request.json
    input_vector = data.get("vector")

    if not input_vector:
        return jsonify({"error": "Missing vector"}), 400

    users_ref = db.collection("users")
    matched_user_id = None

    users = users_ref.stream()
    for user in users:
        user_id = user.id
        doc = user.to_dict()
        encrypted_vector = doc.get("palmVector")
        if not encrypted_vector:
            continue

        try:
            stored_vector = decrypt_vector(encrypted_vector)
            if is_vector_match(stored_vector, input_vector):
                matched_user_id = user_id
                break
        except Exception as e:
            continue  # Skip any error in decryption/format

    if matched_user_id:
        return jsonify({"userId": matched_user_id}), 200
    else:
        return jsonify({"error": "No match found"}), 401
    
def is_vector_match(stored_vector, input_vector, threshold=0.95):
    """
    Compares two vectors using cosine similarity.
    Returns True if similarity is above the threshold.

    :param stored_vector: list of floats
    :param input_vector: list of floats
    :param threshold: similarity threshold (default: 0.95)
    :return: bool
    """
    if not stored_vector or not input_vector:
        return False

    if len(stored_vector) != len(input_vector):
        return False

    similarity = dot(stored_vector, input_vector) / (norm(stored_vector) * norm(input_vector))
    return similarity >= threshold