# token_utils.py

import uuid
from firebase_admin import firestore
from firebase_utils import db
from encryption_utils import encrypt_data as encrypt, decrypt_data as decrypt

def tokenize_value(value):
    token = str(uuid.uuid4())
    encrypted_value = encrypt(value)

    db.collection("tokenVault").document(token).set({
        "original": encrypted_value,
        "createdAt": firestore.SERVER_TIMESTAMP
    })

    return token

def resolve_token(token):
    doc = db.collection("tokenVault").document(token).get()
    if doc.exists:
        encrypted_value = doc.to_dict().get("original")
        return decrypt(encrypted_value)
    return None


