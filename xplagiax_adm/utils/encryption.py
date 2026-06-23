from cryptography.fernet import Fernet
import os
import base64

class EncryptionManager:
    def __init__(self):
        key = "ukpKyvJj1lLnCxRbbqw1GXfFVPFRui_lwxX8vSSeQQs="#os.getenv('ENCRYPTION_KEY')
        if not key:
            key = Fernet.generate_key()
            print(f"Generated new encryption key: {key.decode()}")
        else:
            key = key.encode()
        self.fernet = Fernet(key)
    
    def encrypt(self, data):
        if isinstance(data, str):
            data = data.encode()
        return base64.b64encode(self.fernet.encrypt(data)).decode()
    
    def decrypt(self, encrypted_data):
        encrypted_bytes = base64.b64decode(encrypted_data.encode())
        return self.fernet.decrypt(encrypted_bytes).decode()