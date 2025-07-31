from flask import Blueprint, request, jsonify
from firebase_utils import firestore
from encryption_utils import encrypt_data, decrypt_data
from token_manager import generate_token
from token_utils import tokenize_value
import uuid

user_bp = Blueprint('user', __name__)

@user_bp.route('/register_user', methods=['POST'])
def register_user():
    """
    json expected:
    {
        "email": "
        "fullName": "John Doe",
        "icNumber": "1234567890"
    }
    """
    data = request.json
    user_id = str(uuid.uuid4())

    encrypted_data = {
        'email': encrypt_data(data['email']),
        'fullName': encrypt_data(data['fullName']),
        'icNumber': encrypt_data(data['icNumber']),
        'defaultAccount': ''
    }
    tokenized_data = {k: tokenize_value(v) for k, v in encrypted_data.items()}

    firestore.collection('users').document(user_id).set(tokenized_data)
    return jsonify({'userId': user_id}), 200

@user_bp.route('/user/<user_id>', methods=['GET'])
def get_user_info(user_id):
    """

    Fetch user information by user_id.
    Returns decrypted data including linked accounts.

    """

    doc_ref = firestore.collection('users').document(user_id)
    user_doc = doc_ref.get()
    if not user_doc.exists:
        return jsonify({'error': 'User not found'}), 404

    user_data = user_doc.to_dict()
    decrypted = {
        k: decrypt_data(v) if k != 'defaultAccount' else v
        for k, v in user_data.items()
    }

    accounts = []
    for acc in doc_ref.collection('linkedAccounts').stream():
        acc_data = acc.to_dict()
        accounts.append({
            'id': acc.id,
            'bankName': decrypt_data(acc_data['bankName']),
            'accountType': decrypt_data(acc_data['accountType']),
            'balance': acc_data['balance']
        })

    decrypted['linkedAccounts'] = accounts
    return jsonify(decrypted), 200

@user_bp.route('/user/<user_id>/bank_account', methods=['POST'])
def add_bank_account(user_id):
    """
    json expected:
    {
        "bankName": "Bank A",
        "accountType": "Savings",
        "balance": 1000.0
    }
    """
    data = request.json
    acc_id = str(uuid.uuid4())

    acc_data = {
        'bankName': encrypt_data(data['bankName']),
        'accountType': encrypt_data(data['accountType']),
        'balance': data['balance']
    }

    firestore.collection('users').document(user_id).collection('linkedAccounts').document(acc_id).set(acc_data)
    return jsonify({'accountId': acc_id}), 200

@user_bp.route('/user/<user_id>/default_account', methods=['POST'])
def set_default_account(user_id):
    data = request.json
    firestore.collection('users').document(user_id).update({'defaultAccount': data['accountId']})
    return jsonify({'message': 'Default account set'}), 200
