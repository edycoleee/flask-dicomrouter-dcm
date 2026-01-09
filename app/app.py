import logging
import os
import subprocess
import requests
import tempfile
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, send_file, after_this_request
from flask_restx import Api, Resource, Namespace, fields
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from config import Config

app = Flask(__name__)
Config.init_app()

# --- LOGGER SETTINGS ---
logger = logging.getLogger('DicomLogger')
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(Config.LOG_FILE, maxBytes=1_000_000, backupCount=3)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# --- API SETUP ---
api = Api(app, version='1.1', title='DICOM Gateway API', doc='/api/docs', prefix='/api')
dicom_ns = Namespace('dicom', description='DICOM Router Operations')
api.add_namespace(dicom_ns)

# --- MODELS ---
dicom_model = dicom_ns.model('DicomSend', {
    'study': fields.String(required=True),
    'patientid': fields.String(required=False),
    'accesionnum': fields.String(required=False)
})

# --- SATUSEHAT CONFIG (Sesuaikan di config.py jika perlu) ---
AUTH_URL = "https://api-satusehat.kemkes.go.id/oauth2/v1"
BASE_URL = "https://api-satusehat.kemkes.go.id/fhir-r4/v1"
ORG_ID = "10002xxxx"
CLIENT_ID = "Gzn7YjXvxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
CLIENT_SECRET = "fbPy8SDIkcrxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# --- HELPER FUNCTIONS (SatuSehat) ---

def fetch_ss_token():
    """Mengambil token akses dari SatuSehat OAuth2."""
    token_url = f"{AUTH_URL}/accesstoken?grant_type=client_credentials"
    try:
        resp = requests.post(token_url, data={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}, timeout=15)
        resp.raise_for_status()
        return resp.json().get("access_token"), None
    except Exception as e:
        return None, str(e)

def fhir_get(url, token):
    """Helper untuk melakukan request GET ke FHIR SatuSehat."""
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/fhir+json"}
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        return resp.json(), resp.status_code
    except Exception as e:
        return {"error": str(e)}, 502

# --- HELPER FUNCTIONS (DICOM/PACS) ---

def get_dicom_metadata(study_uid):
    """Mengambil Series dan SOP UID dari PACS."""
    url = f"{Config.DCM4CHEE_URL}/rs/studies/{study_uid}/metadata"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return {
        "series": data[0]["0020000E"]["Value"][0],
        "sop": data[0]["00080018"]["Value"][0]
    }

def download_wado(study_uid, meta, target_path):
    """Download file DICOM asli."""
    params = {
        "requestType": "WADO", "studyUID": study_uid,
        "seriesUID": meta['series'], "objectUID": meta['sop'],
        "contentType": "application/dicom"
    }
    with requests.get(f"{Config.DCM4CHEE_URL}/wado", params=params, stream=True) as r:
        r.raise_for_status()
        with open(target_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

def modify_dicom(file_path, patient_id=None, acc_num=None):
    """Edit tag DICOM menggunakan dcmodify."""
    cmd = ["dcmodify", "--ignore-errors"]
    if patient_id: cmd.extend(["-i", f"(0010,0020)={patient_id}"])
    if acc_num: cmd.extend(["-i", f"(0008,0050)={acc_num}"])
    cmd.append(file_path)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"dcmodify error: {result.stderr}")
    # Hapus file .bak yang otomatis dibuat dcmodify
    if os.path.exists(f"{file_path}.bak"):
        os.remove(f"{file_path}.bak")

def send_to_router(file_path):
    """Kirim file ke Router menggunakan storescu."""
    cmd = [
        "storescu", "-v", "--propose-lossless",
        "-aec", Config.ROUTER_AET, 
        Config.ROUTER_IP, Config.ROUTER_PORT, 
        file_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if "Received Store Response (Success)" not in (result.stdout + result.stderr):
        raise Exception(f"StoreSCU Failed: {result.stderr}")

# --- API ENDPOINTS ---

@dicom_ns.route('/process')
class ProcessDicom(Resource):
    @dicom_ns.expect(dicom_model)
    def post(self):
        """Ambil dari PACS -> Modifikasi (Opsional) -> Kirim ke Router"""
        data = dicom_ns.payload
        study_uid = data['study']
        p_id = data.get('patientid')
        acc = data.get('accesionnum')
        
        local_path = os.path.join(Config.TEMP_DIR, f"proc_{study_uid}.dcm")
        
        try:
            logger.info(f"Processing Study: {study_uid}")
            meta = get_dicom_metadata(study_uid)
            download_wado(study_uid, meta, local_path)
            
            if p_id or acc:
                modify_dicom(local_path, p_id, acc)
                
            send_to_router(local_path)
            return {"status": "success", "study": study_uid}, 200
        except Exception as e:
            logger.error(f"Process failed: {str(e)}")
            return {"status": "error", "message": str(e)}, 500
        finally:
            if os.path.exists(local_path): os.remove(local_path)

@dicom_ns.route('/upload')
class UploadDicom(Resource):
    upload_parser = api.parser()
    upload_parser.add_argument('file', location='files', type=FileStorage, required=True)
    upload_parser.add_argument('patientid', location='form')
    upload_parser.add_argument('accesionnum', location='form')

    @dicom_ns.expect(upload_parser)
    def post(self):
        """Upload file Lokal -> Modifikasi -> Kirim ke Router"""
        args = self.upload_parser.parse_args()
        file = args['file']
        
        filename = secure_filename(file.filename)
        temp_path = os.path.join(Config.TEMP_DIR, f"up_{filename}")
        file.save(temp_path)

        try:
            modify_dicom(temp_path, args.get('patientid'), args.get('accesionnum'))
            send_to_router(temp_path)
            return {"status": "success", "file": filename}, 200
        except Exception as e:
            logger.error(f"Upload process failed: {str(e)}")
            return {"status": "error", "message": str(e)}, 500
        finally:
            if os.path.exists(temp_path): os.remove(temp_path)

@dicom_ns.route('/download/<study_uid>')
class DownloadDicom(Resource):
    def get(self, study_uid):
        """Download file DICOM ke komputer user"""
        local_path = os.path.join(Config.TEMP_DIR, f"dl_{study_uid}.dcm")
        
        @after_this_request
        def cleanup(response):
            if os.path.exists(local_path): os.remove(local_path)
            return response

        try:
            meta = get_dicom_metadata(study_uid)
            download_wado(study_uid, meta, local_path)
            return send_file(local_path, as_attachment=True, download_name=f"{study_uid}.dcm")
        except Exception as e:
            return {"error": str(e)}, 500

@dicom_ns.route('/direct-dcm')
class DirectDicom(Resource):
    @dicom_ns.expect(api.model('Direct', {'study': fields.String(required=True)}))
    def post(self):
        """Relay Murni: Download dari PACS langsung kirim ke Router"""
        data = dicom_ns.payload
        study_uid = data['study']
        local_path = os.path.join(Config.TEMP_DIR, f"relay_{study_uid}.dcm")

        try:
            logger.info(f"[RELAY] Memulai direct transfer untuk: {study_uid}")
            
            # 1. Metadata & Download
            meta = get_dicom_metadata(study_uid)
            download_wado(study_uid, meta, local_path)
            
            # 2. Kirim Langsung (Tanpa modify_dicom)
            send_to_router(local_path)
            
            return {"status": "success", "message": "Relay berhasil", "study": study_uid}, 200
        except Exception as e:
            logger.error(f"[RELAY FAILED] {str(e)}")
            return {"status": "error", "message": str(e)}, 500
        finally:
            if os.path.exists(local_path): 
                os.remove(local_path)

@dicom_ns.route('/imageid/<string:acsn>')
@dicom_ns.doc(params={'acsn': 'Accession Number dari PACS/SatuSehat'})
class ImageId(Resource):
    def get(self, acsn):
        """Ambil ImagingStudy ID dari SatuSehat berdasarkan Accession Number"""
        token, err = fetch_ss_token()
        if err:
            logger.error(f"Auth SatuSehat failed: {err}")
            return {"status": "error", "message": "Auth SatuSehat failed", "detail": err}, 502
        
        identifier_system = f"http://sys-ids.kemkes.go.id/acsn/{ORG_ID}"
        url = f"{BASE_URL}/ImagingStudy?identifier={identifier_system}|{acsn}"
        
        data, status = fhir_get(url, token)
        
        if status != 200:
            return {"status": "error", "detail": data}, status

        if data.get("resourceType") == "Bundle":
            entries = data.get("entry") or []
            for e in entries:
                res = e.get("resource") or {}
                if res.get("resourceType") == "ImagingStudy":
                    # Fix: Penggunaan logger.info yang benar
                    logger.info(f"ImagingStudy found: {res.get('id')}")
                    return {
                        "status": "success",
                        "imagingStudy_id": res.get("id"),
                        "patient_reference": res.get("subject", {}).get("reference")
                    }, 200

        logger.error(f"No ImagingStudy found for Accession Number: {acsn}")    
        return {"status": "error", "message": "No ImagingStudy found for this Accession Number"}, 404

@app.route("/")
def index():
    return render_template("dcmpage.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)