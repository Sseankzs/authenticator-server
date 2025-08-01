import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Write the JSON key to a temp file
firebase_key = os.environ.get("FIREBASE_KEY")
key_path = "temp_service_account.json"

if firebase_key:
    with open(key_path, "w") as f:
        json.dump(json.loads(firebase_key), f)

    cred = credentials.Certificate(key_path)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
else:
    raise RuntimeError("FIREBASE_KEY environment variable not set")
