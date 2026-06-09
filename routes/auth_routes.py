
from flask import Blueprint, request, jsonify
from services.auth_service import check_login_credentials

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/api/login', methods=['POST'])
def login():
    # 1. Mengambil data berformat JSON yang dikirim oleh pengguna
    data = request.get_json()
    
    # 1. Mengambil data berformat JSON yang dikirim oleh pengguna
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({
            "success": False,
            "message": "Username atau Password salah, silakan coba lagi!"
        })
        
    input_username = data.get('username') 
    input_password = data.get('password') 
    
    # 2. Melempar data ke auth_service untuk dicek kebenarannya
    result = check_login_credentials(input_username, input_password)
    
    # 3. Memberikan respon balik ke pengguna berdasarkan hasil pengecekan
    if result["success"]:
        return jsonify(result), 200
    else:
        return jsonify({"error": result["message"]}), 401
