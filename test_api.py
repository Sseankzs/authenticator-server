# test_api.py
import requests
from datetime import datetime

BASE_URL = "http://localhost:5000"

user_id = "Kong Zhi Syuen"
bankAccount = "maybank"
bankAccountType = "savings"
account_id = "hongleongsavings"
transaction_id = "jysedfvd124-123jh12v3h"
palm_vector = [0.12, 0.34, 0.18, 0.45, 0.67, 0.23]  # Example palm vector

def post(path, data):
    res = requests.post(f"{BASE_URL}{path}", json=data)
    try:
        print(f"POST {path} → {res.status_code}\n", res.json(), "\n")
        return res.json()
    except Exception:
        print(f"POST {path} → {res.status_code}\n", res.text, "\n")

def get(path):
    res = requests.get(f"{BASE_URL}{path}")
    try:
        print(f"GET {path} → {res.status_code}\n", res.json(), "\n")
        return res.json()
    except Exception:
        print(f"GET {path} → {res.status_code}\n", res.text, "\n")

# 1. Register user [tested]
#Expect: {"message": "User registered"}, Database should have user data encrypted
post("/register_user", {
    "userId": user_id,
    "email": "user@example.com",
    "fullName": "Alice Tan",
    "icNumber": "900101-01-1234",
    "phoneNumber": "0123456789"
})


# 2. Register palm vector [tested]
# Expect: {"message": "Palm vector registered"}, Database should have palm vector encrypted
post("/register_palm", {
    "userId": user_id,
    "vector": palm_vector
})

# 3. Add bank account [tested]
# Expect: {"message": "Bank account added"}, Database should have bank account data encrypted
post("/add_bank_account", {
    "userId": user_id,
    "bankAccountId": account_id,
    "bankName": "maybank",
    "accountType": "savings",
    "balance": 1000.0
})

# 4. Set default account [tested]
# Expect: {"message": "Default account set"}, Database should update default account
post("/set_default_account", {
    "userId": user_id,
    "accountId": account_id,
    "bankName": "maybank",
    "accountType": "savings"
})

# 5. Add transaction (simulate merchant)
post("/merchant/add_transaction", {
    "userId": user_id,
    "accountId": account_id,
    "transactionId": transaction_id,
    "amount": 15.0,
    "category": "Food",
    "merchant": "KFC",
    "timestamp": datetime.utcnow().isoformat(),
    "vector": palm_vector  # Use the same palm vector for verification
})

# 6. Get user info (Profile Page)
get(f"/get_user_info/{user_id}")

# 7. Get transaction history (Transaction Page)
get(f"/transactions/{user_id}")

# 8. Get dashboard summary (Dashboard Page)
get(f"/dashboard/{user_id}")

# 9. Simulate biometric vector verification → should return token
token_response = post("/verify_vector", {
    "vector": palm_vector
})
token = token_response.get("token")

