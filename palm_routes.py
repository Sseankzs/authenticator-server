from flask import Blueprint, request, jsonify
from firebase_admin import firestore
from uuid import uuid4
from encryption_utils import encrypt_vector  # Replace with your actual function

db = firestore.client()
bp = Blueprint('palm', __name__)

@bp.route("/register_palm", methods=["POST"])
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
