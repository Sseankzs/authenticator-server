# populate_transactions.py
import requests
import random
from datetime import datetime, timedelta
import argparse

BASE_URL = "https://authenticator-server-87a8.onrender.com"  # adjust if deployed

user_id = "uZsYmasM5B3dVXTYjt3J"
palm_vector = [0.12, 0.34, 0.18, 0.45, 0.67, 0.23]  # Example palm vector


CATEGORIES = ['Groceries', 'Food & Drink', 'Bills', 'Transport', 'Others']
MERCHANTS = ["KFC", "McD", "Tesco", "Grab", "Shell", "7-Eleven", "Parkson", "CinemaX", "GymCo", "CafeBrew"]


def post(path, data):
    res = requests.post(f"{BASE_URL}{path}", json=data)
    try:
        print(f"POST {path} → {res.status_code}\n", res.json(), "\n")
        return res.json()
    except Exception:
        print(f"POST {path} → {res.status_code}\n", res.text, "\n")

post("/register_palm", {
    "userId": user_id,
    "vector": palm_vector
})

def random_timestamp_within_last_month():
    now = datetime.utcnow()
    past = now - timedelta(days=30)
    delta = now - past
    random_seconds = random.randint(0, int(delta.total_seconds()))
    ts = past + timedelta(seconds=random_seconds)
    return ts.isoformat() + "Z"  # ISO with Z

def post_transaction(user_id, account_id):
    transaction_id = f"trx_{random.randint(100000, 999999)}"
    amount = round(random.uniform(5.0, 200.0), 2)
    category = random.choice(CATEGORIES)
    merchant = random.choice(MERCHANTS)
    payload = {
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
    parser = argparse.ArgumentParser(description="Populate random transactions")
    parser.add_argument("--user", required=True, help="User ID")
    parser.add_argument("--account", required=True, help="Account ID")
    parser.add_argument("-n", type=int, default=40, help="Number of transactions")
    parser.add_argument("--base", default=BASE_URL, help="Base URL of server")
    args = parser.parse_args()

    global BASE_URL
    BASE_URL = args.base.rstrip("/")

    for i in range(args.n):
        post_transaction(args.user, args.account)

if __name__ == "__main__":
    main()
