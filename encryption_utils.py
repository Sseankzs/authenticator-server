from cryptography.fernet import Fernet
import base64
import os
import json

key = base64.urlsafe_b64encode(os.environ["FERNET_KEY"].encode())
cipher = Fernet(key)

def encrypt_data(data: str) -> str:
    return cipher.encrypt(data.encode()).decode()

# Decrypt a string
def decrypt_data(data: str) -> str:
    return cipher.decrypt(data.encode()).decode()

# Encrypt a list of floats (vector)
def encrypt_vector(vector: list[float]) -> str:
    json_string = json.dumps(vector)
    return encrypt_data(json_string)

# Decrypt a vector string back to list of floats
def decrypt_vector(encrypted_str: str) -> list[float]:
    json_string = decrypt_data(encrypted_str)
    return json.loads(json_string)