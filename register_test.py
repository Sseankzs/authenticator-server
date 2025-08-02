import requests

url = "http://localhost:5000/register_vector"
payload = {
    "userId": "uZsYmasM5B3dVXTYjt3J",
    "vector": [0.231231, 0.123123, 0.321321, 0.456456, 0.654654, 0.789789],
    "mode": "palm"  # or "face"
}

response = requests.post(url, json=payload)
print(response.status_code)
print(response.json())
