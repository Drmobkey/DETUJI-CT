from pydicom import pydicom
import cv2
import numpy as np
import pydicom
from PIL import Image
from config import Config

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.',1)[1].lower() in Config.ALLOWED_EXTENSIONS

def is_not_medical_image(file_stream, threshold= 15.0):

    # 1. Baca gambar dari memory stream (karena file belum disimpan)
    file_bytes = np.frombuffer(file_stream.read(), np.uint8)
    img_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    # 2. Reset posisi pointer file ke awal agar bisa dibaca lagi nanti
    file_stream.seek(0)
    
    if img_bgr is None:
        return True
    
    # 3. Pecah gambar menjadi 3 channel: Blue, Green, Red
    b,g,r = cv2.split(img_bgr)
    
    # 4. Hitung selisih antar channel warna
    diff_rg = np.abs(r.astype(np.int16) - g.astype(np.int16))
    diff_rb = np.abs(r.astype(np.int16) - b.astype(np.int16))
    diff_gb = np.abs(g.astype(np.int16) - b.astype(np.int16))
    
    # 4. Hitung rata-rata deviasi warna gambar
    mean_diff = (np.mean(diff_rg) + np.mean(diff_rb) + np.mean(diff_gb)) / 3.0
    
    # Jika rata-rata selisih warna di atas threshold, artinya gambar terlalu berwarna
    return mean_diff > threshold

def process_upload_validation(file):
    if file.filename == '':
        return{
            "success": False, 
            "message": "Nama file tidak boleh kosong!", 
            "status_code": 400
        }
    
    if not allowed_file(file.filename):
        return {
            "success": False, 
            "message": f"Format file tidak diizinkan! Hanya menerima format: {', '.join(Config.ALLOWED_EXTENSIONS)}", 
            "status_code": 400
        }
    return {"success": True, "status_code": 200}

def read_image_file(file_path):
    
    ext = file_path.split('.')[-1].lower()
    
    # Jika filenya adalah format rontgen medis asli (DICOM)
    if ext == 'dcm':
        ds = pydicom.dcmread(file_path)
        img_array = ds.pixel_array
        
        # Konversi ke uint8 (skala 0-255) agar bisa diolah oleh OpenCV
        img_array = ((img_array - np.min(img_array)) / (np.max(img_array) - np.min(img_array)) * 255).astype(np.uint8)
        
        # DICOM biasanya grayscale, kita ubah ke RGB (3 channel) sesuai syarat MobileNet
        img_rgb = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
        return img_rgb
    
    # Jika filenya adalah gambar standar (PNG/JPG)
    else:
        # Membaca gambar dengan OpenCV (Default: BGR)
        img_bgr = cv2.imread(file_path)
        
        # Diubah ke format RGB sesuai fungsi load_image di notebook Anda
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        return img_rgb
    
def preprocess_for_mobilenet(file_path, target_size=(256,256)):
    
     try:
         # 1. Baca gambar sesuai ekstensinya
         img = read_image_file(file_path)
         
         # 2. Resize gambar menjadi 256x256 sesuai bentuk input Netron [?, 256, 256, 3]
         img_resized = cv2.resize(img, target_size)
         
         # 3. Normalisasi piksel (membagi dengan 255.0) seperti rumus notebook Anda
         img_normalized = img_resized / 255.0
         img_normalized = img_normalized.astype(np.float32)
         
         # 4. Expand dimensi dari (256, 256, 3) menjadi (1, 256, 256, 3)
         # Ini dilakukan karena Keras menerima input dalam bentuk batch/kumpulan gambar
         img_final = np.expand_dims(img_normalized, axis=0)
         
         return {"success": True, "processed_data": img_final}
     
     except Exception as e:
         return {"success": False, "message": f"Gagal memproses gambar: {str(e)}",}
        
         
         
    