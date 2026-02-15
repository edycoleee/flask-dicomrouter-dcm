import os
from dotenv import load_dotenv

load_dotenv()  # Load .env file

class Config:
    # --- DCM4CHEE ---
    DCM4CHEE_URL = os.getenv("DCM4CHEE_URL")
    PACS_AET = os.getenv("PACS_AET", "DCM4CHEE")
    PACS_USER = os.getenv("PACS_USER")
    PACS_PASSWORD = os.getenv("PACS_PASSWORD")

    # --- ROUTER STORESCU ---
    ROUTER_IP = os.getenv("ROUTER_IP")
    ROUTER_PORT = os.getenv("ROUTER_PORT")
    ROUTER_AET = os.getenv("ROUTER_AET")

    # --- LOGGING ---
    LOG_FILE = os.getenv("LOG_FILE", "app_dicom.log")

    # --- TEMP DIRECTORY ---
    TEMP_DIR = os.getenv("TEMP_DIR", "/tmp/dicom_gateway_tmp")

    # --- SATUSEHAT ---
    AUTH_URL = os.getenv("AUTH_URL")
    BASE_URL = os.getenv("BASE_URL")
    ORG_ID = os.getenv("ORG_ID")
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")

    @classmethod
    def init_app(cls):
        """Pastikan folder temp tersedia."""
        if not os.path.exists(cls.TEMP_DIR):
            os.makedirs(cls.TEMP_DIR, exist_ok=True)
