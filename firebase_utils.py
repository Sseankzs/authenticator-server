# firebase_utils.py
import firebase_admin
from firebase_admin import credentials, firestore

from cryptography.fernet import Fernet
import os

fernet = Fernet(os.environ["FERNET_KEY"])

def encrypt(data):
    return fernet.encrypt(data.encode()).decode()

def decrypt(token):
    return fernet.decrypt(token.encode()).decode()

def init_firebase(cred_path=None):
    if not firebase_admin._apps:
        if cred_path:
            cred = credentials.Certificate(cred_path)
        else:
            cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
    return firestore.client()
