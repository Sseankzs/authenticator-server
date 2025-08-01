# app.py

from flask import Flask, request, jsonify
from firebase_utils import init_firebase
from vector_matcher import match_vector
import config
from user_routes import user_bp
from merchant_routes import merchant_bp
from palm_routes import palm_bp
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
db = init_firebase(config.FIREBASE_CRED_PATH)

app.register_blueprint(user_bp)
app.register_blueprint(merchant_bp)
app.register_blueprint(palm_bp)

if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
