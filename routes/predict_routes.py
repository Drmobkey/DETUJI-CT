import os
import uuid
import time
from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from config import Config
from services.ai_service import process_upload_validation, run_ai_prediction

predict_bp = Blueprint('predict_bp', __name__)


def auto_clean_old_files(folder_path, max_age_days=7):
    """
    Fungsi utilitas untuk menghapus file yang umurnya sudah lebih dari 7 hari di server.
    """
    now = time.time()
    cutoff = now - (max_age_days * 86400) # 86400 adalah jumlah detik dalam 1 hari
    
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            # Ambil waktu modifikasi terakhir file tersebut
            file_modified_time = os.path.getmtime(file_path)
            
            # Jika waktu modifikasi file lebih tua daripada batas cutoff, hapus!
            if file_modified_time < cutoff:
                try:
                    os.remove(file_path)
                    print(f"--- [AUTO CLEAN] Menghapus file usang: {filename} ---")
                except Exception as e:
                    print(f"Gagal menghapus file {filename}: {e}")

@predict_bp.route('/api/predict', methods=['POST'])
def predict():
    if 'files' not in request.files:
        return jsonify({"error": "Permintaan tidak sah, tidak ada bagian file!"}), 400
    
    files = request.files.getlist('files')
    
    if len(files) == 0 or files[0].filename == '':
        return jsonify({"error": "Tidak ada file yang dipilih!"}), 400
        
    if len(files) > 15:
        return jsonify({"error": "Maksimal 15 file gambar yang dapat diproses sekaligus!"}), 400
    
    nama_pasien = request.form.get('nama_pasien', 'Anonim')
    no_rm = request.form.get('no_rm', '-')
    
    details = []
    tumor_count = 0
    normal_count = 0
    confidence_sum = 0
    
    for file in files:
        validation_result = process_upload_validation(file)
        if not validation_result["success"]:
            return jsonify ({"error": f"File {file.filename} tidak valid: {validation_result['message']}"}), validation_result["status_code"]
        
        filename = secure_filename(file.filename)
        # Berikan prefix unik agar nama file tidak bentrok jika namanya sama
        unique_filename = f"{uuid.uuid4().hex[:6]}_{filename}"
        filepath = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
        file.save(filepath)
        
        # PANGGIL AI UNTUK PREDIKSI NYATA
        ai_result = run_ai_prediction(filepath)
        
        if ai_result["success"]:
            prediction = ai_result["prediction"]
            confidence = ai_result["confidence"]
            
            if "Tumor" in prediction:
                tumor_count += 1
            else:
                normal_count += 1
                
            confidence_sum += confidence
            
            details.append({
                "saved_filename": unique_filename,
                "original_filename": filename,
                "prediction": prediction,
                "confidence": min(round(confidence * 100, 2), 99.99),
                "is_doubtful": ai_result.get("is_doubtful", False),
                "message": ai_result.get("message", "Berhasil dianalisis")
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Gagal memproses file {filename}: {ai_result.get('message', 'Terjadi kesalahan')}"
            }), 400
            
    # Penentuan Mayoritas
    if tumor_count >= normal_count:
        overall_prediction = "Tumor Ginjal"
    else:
        overall_prediction = "Normal"
        
    avg_confidence = (confidence_sum / len(files)) if len(files) > 0 else 0
    summary_text = f"Dari {len(files)} citra yang dipindai, {tumor_count} terdeteksi mengarah ke indikasi tumor, dan {normal_count} terdeteksi normal."
    
    return jsonify({
        "status": "success",
        "analysis_id": f"DETUJI-{uuid.uuid4().hex[:8].upper()}",
        "nama_pasien": nama_pasien,
        "no_rm": no_rm,
        "prediction": overall_prediction, # Disamakan agar tidak merusak field legacy di frontend jika masih dipakai
        "overall_prediction": overall_prediction,
        "confidence": min(round(avg_confidence * 100, 2), 99.99),
        "total_files": len(files),
        "tumor_count": tumor_count,
        "normal_count": normal_count,
        "summary_text": summary_text,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message": summary_text,
        "details": details
    }), 200