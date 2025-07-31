# firebase_utils.py
import firebase_admin
from firebase_admin import credentials, firestore

def init_firebase(cred_path=None):
    if not firebase_admin._apps:
        if cred_path:
            cred = credentials.Certificate(cred_path)
        else:
            cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
    return firestore.client()
