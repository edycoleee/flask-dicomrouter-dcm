import os
import tempfile

class Config:
    # Mengambil dari Environment Variable, jika tidak ada pakai default (fallback)
    DCM4CHEE_URL = os.getenv("DCM4CHEE_URL", "http://192.10.10.23:8081/dcm4chee-arc/aets/DCM4CHEE")
    
    ROUTER_IP = os.getenv("ROUTER_IP", "192.10.10.51")
    ROUTER_PORT = os.getenv("ROUTER_PORT", "11112")
    ROUTER_AET = os.getenv("ROUTER_AET", "DCMROUTER")
    
    LOG_FILE = os.getenv("LOG_FILE", "app_dicom.log")
    
    # Menyesuaikan dengan path di dalam Docker (lebih konsisten)
    TEMP_DIR = os.getenv("TEMP_DIR", "/tmp/dicom_gateway_tmp")

    @classmethod
    def init_app(cls):
        """Memastikan folder temporary tersedia saat aplikasi start"""
        if not os.path.exists(cls.TEMP_DIR):
            os.makedirs(cls.TEMP_DIR, exist_ok=True)