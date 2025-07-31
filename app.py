# app.py

from flask import Flask, request, jsonify
from firebase_utils import init_firebase
from token_manager import TokenManager
from vector_matcher import match_vector
import config
from user_routes import bp as user_bp
from merchant_routes import bp as merchant_bp
from palm_routes import bp as palm_bp



app = Flask(__name__)
db = init_firebase(config.FIREBASE_CRED_PATH)
token_manager = TokenManager(db)

app.register_blueprint(user_bp)
app.register_blueprint(merchant_bp)
app.register_blueprint(palm_bp)

@app.route("/verify_vector", methods=["POST"])
def verify_vector():
    data = request.json
    input_vector = data.get("vector")

    if not input_vector:
        return jsonify({"error": "Missing vector"}), 400

    user_id = match_vector(input_vector, db)
    if not user_id:
        return jsonify({"error": "No match found"}), 404

    token = token_manager.generate_token(user_id)
    return jsonify({"token": token}), 200

@app.route("/check_token", methods=["POST"])
def check_token():
    data = request.json
    token = data.get("token")

    if not token:
        return jsonify({"error": "Missing token"}), 400

    user_id = token_manager.verify_token(token)
    if not user_id:
        return jsonify({"error": "Invalid or expired token"}), 401

    return jsonify({"userId": user_id}), 200

@app.route("/invalidate_token", methods=["POST"])
def invalidate_token():
    data = request.json
    token = data.get("token")

    if not token:
        return jsonify({"error": "Missing token"}), 400

    token_manager.invalidate_token(token)
    return jsonify({"status": "Token invalidated"}), 200

if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
