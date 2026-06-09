from config import Config

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.',1)[1].lower() in Config.ALLOWED_EXTENSIONS

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