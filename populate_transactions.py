# populate_transactions.py
import requests
import random
from datetime import datetime, timedelta

BASE_URL = " http://127.0.0.1:5000"  # adjust if deployed

user_id = "uZsYmasM5B3dVXTYjt3J"
palm_vector = [0.12, 0.34, 0.18, 0.45, 0.67, 0.23]  # Example palm vector
# res = requests.post(f"{BASE_URL}/register_palm", json={
#     "userId": user_id,
#     "vector": palm_vector
# })
# if res.ok:
#         print(f"[OK] palm vector registered for {user_id}")
# else:
#         print(f"[ERR] palm vector registration failed for {user_id}")


CATEGORIES = ['Groceries', 'Food & Drink', 'Bills', 'Transport', 'Others']
MERCHANTS = ["KFC", "McD", "Tesco", "Grab", "Shell", "7-Eleven", "Parkson", "CinemaX", "GymCo", "CafeBrew"]

def random_timestamp_within_last_month():
    now = datetime.utcnow()
    past = now - timedelta(days=30)
    delta = now - past
    random_seconds = random.randint(0, int(delta.total_seconds()))
    ts = past + timedelta(seconds=random_seconds)
    return ts.isoformat() + "Z"  # ISO with Z

def post_transaction():
    transaction_id = f"trx_{random.randint(100000, 999999)}"
    amount = round(random.uniform(5.0, 200.0), 2)
    category = random.choice(CATEGORIES)
    merchant = random.choice(MERCHANTS)
    payload = {
        "vector": palm_vector,
        "transactionId": transaction_id,
        "amount": amount,
        "category": category,
        "merchant": merchant,
        "timestamp": random_timestamp_within_last_month()
    }
    res = requests.post(f"{BASE_URL}/merchant/add_transaction", json=payload)
    if res.ok:
        print(f"[OK] {transaction_id}: {category} @{merchant} RM{amount} → {res.status_code}")
    else:
        print(f"[ERR] {transaction_id}: {res.status_code} {res.text.strip()}")

def main():
    # Number of transactions to create
    num_transactions = 40
    
    print(f"Creating {num_transactions} transactions for user {user_id}")
    print(f"Using palm vector: {palm_vector}")
    print("-" * 50)
    
    for i in range(num_transactions):
        post_transaction()

if __name__ == "__main__":
    main()
