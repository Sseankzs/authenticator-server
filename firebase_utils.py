# firebase_utils.py
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

db = None

def init_firebase(cred_path="serviceAccountKey.json"):
    global db
    if not firebase_admin._apps:
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
        elif os.environ.get("FIREBASE_KEY"):
            # Load from environment (Render deployment)
            key_data = json.loads(os.environ["FIREBASE_KEY"])
            cred = credentials.Certificate(key_data)
        else:
            # Fallback to default credentials (e.g., GCP)
            cred = credentials.ApplicationDefault()

        firebase_admin.initialize_app(cred)

    db = firestore.client()
    return db

# Automatically initialize if running locally
if not firebase_admin._apps:
    init_firebase()