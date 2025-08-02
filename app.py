# app.py

from flask import Flask, request, jsonify
from firebase_utils import init_firebase
import config
from user_routes import user_bp
from merchant_routes import merchant_bp
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
db = init_firebase(config.FIREBASE_CRED_PATH)

app.register_blueprint(user_bp)
app.register_blueprint(merchant_bp)

if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
