# test_api.py
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

user_id = "user_1"
account_id = "bacc_1"
transaction_id = "trx_001"

def post(path, data):
    res = requests.post(f"{BASE_URL}{path}", json=data)
    try:
        print(f"{path} → {res.status_code}\n", res.json(), "\n")
    except requests.exceptions.JSONDecodeError:
        print(f"{path} → {res.status_code}\n", res.text, "\n")

def get(path):
    res = requests.get(f"{BASE_URL}{path}")
    print(f"{path} → {res.status_code}\n", res.json(), "\n")

# 1. Register User
post("/register", {
    "userId": user_id,
    "email": "user@example.com",
    "fullName": "Alice Tan",
    "icNumber": "900101-01-1234",
    "phoneNumber": "0123456789"
})

# 2. Register Palm Vector
post("/register_palm", {
    "userId": user_id,
    "vector": [0.12, 0.34, 0.56, 0.78]
})

# 3. Add Bank Account
post(f"/user/{user_id}/add_account", {
    "bankAccountId": account_id,
    "bankName": "Maybank",
    "accountType": "Savings",
    "balance": 1000.0
})

# 4. Set Default Account
post(f"/user/{user_id}/set_default_account", {
    "defaultAccount": account_id
})

# 5. Add Transaction (Merchant)
post("/merchant/add_transaction", {
    "userId": user_id,
    "accountId": account_id,
    "transactionId": transaction_id,
    "amount": 15.0,
    "category": "Food",
    "merchant": "KFC",
    "status": "success",
    "timestamp": datetime.utcnow().isoformat()
})

# 6. Get User Info
get(f"/user/{user_id}")

# 7. Simulate /verify_vector
post("/verify_vector", {
    "vector": [0.12, 0.34, 0.56, 0.78]
})

# 8. Simulate /check_token (you'll need to manually insert token here after getting it)
# token = "paste_token_here"
# post("/check_token", {"token": token})

# 9. Simulate /invalidate_token (optional)
# post("/invalidate_token", {"token": token})
