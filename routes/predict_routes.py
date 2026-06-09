import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from config import Config
from services.ai_service import process_upload_validation

predict_bp = Blueprint('predict_bp', __name__)

@predict_bp.route('/api/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({"error": "Permintaan tidak sah, tidak ada bagian file!"}), 400
    
    file = request.files['file']
    
    validation_result = process_upload_validation(file)
    if not validation_result["success"]:
        return jsonify ({"error": validation_result["message"]}),validation_result["status_code"]
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
    
    file.save(filepath)
    
    return jsonify({
        "status":"success",
        "message" : "File gambar CT Scan berhasil diunggah dan divalidasi",
        "saved_filename" : filename,
        "prediction_mock": "Normal / Tumor (Modul AI akan diproses di tahap berikutnya)"
        
    }),200