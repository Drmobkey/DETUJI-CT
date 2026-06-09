import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from config import Config
from services.ai_service import process_upload_validation, run_ai_prediction

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
    
    # PANGGIL AI UNTUK PREDIKSI NYATA
    ai_result = run_ai_prediction(filepath)
    
    if ai_result["success"]:
        return jsonify({
            "status": "success",
            "message": "File gambar CT Scan berhasil dianalisis",
            "saved_filename": filename,
            "prediction": ai_result["prediction"],
            "confidence": ai_result["confidence"]
        }), 200
    else:
        error_response = {
            "status": "error",
            "message": ai_result.get("message", "Gagal memproses file gambar CT Scan"),
            "saved_filename": filename
        }
        if "confidence" in ai_result:
            error_response["confidence"] = ai_result["confidence"]
        return jsonify(error_response), 400