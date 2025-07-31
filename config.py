# config.py

import os

# Path to Firebase service account key (optional if using env)
FIREBASE_CRED_PATH = os.getenv("FIREBASE_CRED_PATH", "serviceAccountKey.json")

# Flask settings
HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
