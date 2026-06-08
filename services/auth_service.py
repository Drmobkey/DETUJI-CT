from config import config

def check_login_credentials(username,password):
    if username == config.ADMIN_USERNAME and password == config.ADMIN_PASSWORD:
        return{
            "success" : True,
            "message" : "Login successfully"
        }
    else:
        return{
            "success": False,
            "message": "Username atau Password salah, silakan coba lagi!"
        }
