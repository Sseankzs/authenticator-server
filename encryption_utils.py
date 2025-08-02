import uuid
from cryptography.fernet import Fernet
import base64
import os
import json
from dotenv import load_dotenv
from firebase_utils import db

load_dotenv()

raw_key = os.environ.get("FERNET_KEY")
if not raw_key:
    raise ValueError("FERNET_KEY not found in environment.")

try:
    key = base64.urlsafe_b64decode(raw_key)
    if len(key) != 32:
        raise ValueError("FERNET_KEY is not 32 bytes after decoding.")
except Exception as e:
    raise ValueError(f"Invalid FERNET_KEY: {e}")
cipher = Fernet(base64.urlsafe_b64encode(key))

def encrypt_data(data: str) -> str:
    return cipher.encrypt(data.encode()).decode()

# Decrypt a string
def decrypt_data(data: str) -> str:
    return cipher.decrypt(data.encode()).decode()

# tokenizes a list of floats (vector)
def tokenize_vector(vector: list[float]) -> str:
    vector_token = str(uuid.uuid4())

    doc_data = {
        "vector": vector,
    }

    db.collection("tokenVault").document(vector_token).set(doc_data)


# Resolves a vector token back to list of floats
# Call this function after identifying the vector in the toke vault
def resolve_vector_token(token: str) -> list[float]:
    doc = db.collection("tokenVault").document(token).get()
    if not doc.exists:
        raise ValueError("Vector token not found in database.")
    else:
        return doc.to_dict()