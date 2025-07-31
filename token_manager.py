# token_manager.py
import uuid
from datetime import datetime, timedelta

class TokenManager:
    def __init__(self, db):
        self.db = db

    def generate_token(self, user_id):
        token = str(uuid.uuid4())
        expiry = datetime.timezone.utc() + timedelta(minutes=5)
        data = {
            "userId": user_id,
            "token": token,
            "createdAt": datetime.timezone.utc(),
            "expiresAt": expiry,
            "valid": True
        }
        self.db.collection("tokenMappings").document(token).set(data)
        return token

    def verify_token(self, token):
        doc = self.db.collection("tokenMappings").document(token).get()
        if not doc.exists:
            return False
        data = doc.to_dict()
        if not data["valid"] or datetime.utcnow() > data["expiresAt"].replace(tzinfo=None):
            return False
        return data["userId"]

    def invalidate_token(self, token):
        self.db.collection("tokenMappings").document(token).update({"valid": False})
