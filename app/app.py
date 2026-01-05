import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, jsonify
from flask_restx import Api, Resource, Namespace, fields
import requests
import subprocess
import os
from werkzeug.datastructures import FileStorage

app = Flask(__name__)

# --- KONFIGURASI LOGGER ---
log_filename = 'app_dicom.log'
log_handler = RotatingFileHandler(log_filename, maxBytes=150000, backupCount=1)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)

logger = logging.getLogger('DicomLogger')
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# --- FLASK-RESTX API CONFIGURATION ---
api = Api(app, 
          version='1.0', 
          title='DICOM Gateway API',
          description='Gateway untuk Manipulasi dan Pengiriman Gambar DICOM',
          doc='/docs', 
          prefix='/api')

dicom_ns = Namespace('dicom', description='Operasi DICOM ke Router')
api.add_namespace(dicom_ns)

# --- SYSTEM CONFIGURATION ---
DCM4CHEE_URL = "http://192.10.10.23:8081/dcm4chee-arc/aets/DCM4CHEE"
ROUTER_IP = "192.10.10.28"
ROUTER_PORT = "11112"
ROUTER_AET = "DCMROUTER"

# --- MODELS ---
dicom_model = dicom_ns.model('DicomSend', {
    'study': fields.String(required=True, example='1.3.46...'),
    'patientid': fields.String(required=True, example='P00001349322'),
    'accesionnum': fields.String(required=True, example='202512300002')
})

direct_model = dicom_ns.model('DirectSend', {
    'study': fields.String(required=True, example='1.3.46...')
})

# --- HELPER FUNCTIONS ---
def cleanup_files(filename):
    for ext in ["", ".bak"]:
        path = f"{filename}{ext}"
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                logger.error(f"Gagal menghapus {path}: {e}")

# --- WEB UI ROUTES ---
@app.route("/")
def index():
    return render_template("dcmpage.html")

# --- PARSER UNTUK UPLOAD FILE ---
upload_parser = dicom_ns.parser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True, help='File DICOM (.dcm)')
upload_parser.add_argument('patientid', location='form', type=str, required=True, help='Patient ID Baru')
upload_parser.add_argument('accesionnum', location='form', type=str, required=True, help='Accession Number Baru')


# --- API ENDPOINTS ---
@dicom_ns.route('/send-dcm')
class SendDicom(Resource):
    @dicom_ns.expect(dicom_model)
    def post(self):
        data = dicom_ns.payload
        study_uid = data.get('study')
        patient_id = data.get('patientid')
        acc_num = data.get('accesionnum')

        local_file = f"temp_{study_uid}.dcm"
        
        try:
            # 1. Ambil Metadata
            logger.info(f"[STEP 1] Mengambil Metadata dari DCM4CHEE untuk Study: {study_uid}")
            meta_url = f"{DCM4CHEE_URL}/rs/studies/{study_uid}/metadata"
            meta_resp = requests.get(meta_url, timeout=15)
            meta_resp.raise_for_status()
            metadata = meta_resp.json()
            
            series_uid = metadata[0]["0020000E"]["Value"][0]
            sop_uid = metadata[0]["00080018"]["Value"][0]
            logger.info(f"Metadata didapat: Series={series_uid}, SOP={sop_uid}")

            # 2. Download DICOM via WADO
            logger.info(f"[STEP 2] Downloading file DICOM via WADO...")
            wado_url = f"{DCM4CHEE_URL}/wado"
            params = {
                "requestType": "WADO", "studyUID": study_uid,
                "seriesUID": series_uid, "objectUID": sop_uid,
                "contentType": "application/dicom"
            }
            img_resp = requests.get(wado_url, params=params, stream=True)
            img_resp.raise_for_status()
            with open(local_file, 'wb') as f:
                for chunk in img_resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"Download selesai: {local_file}")

            # 3. dcmodify (Edit Tag DICOM)
            logger.info(f"[STEP 3] Menjalankan dcmodify untuk PatientID: {patient_id} & Acc: {acc_num}")
            modify_cmd = [
                "dcmodify", "--ignore-errors",
                "-i", f"(0010,0020)={patient_id}",
                "-i", f"(0008,0050)={acc_num}",
                local_file
            ]
            mod_result = subprocess.run(modify_cmd, capture_output=True, text=True)
            if mod_result.returncode != 0:
                logger.error(f"dcmodify error: {mod_result.stderr}")
                raise Exception("Gagal modifikasi metadata DICOM")
            logger.info("Modifikasi metadata berhasil.")

            # 4. storescu (Kirim ke Router)
            logger.info(f"[STEP 4] Mengirim ke Router {ROUTER_IP}:{ROUTER_PORT} via storescu")
            send_cmd = ["storescu", "-v", "-aec", ROUTER_AET, ROUTER_IP, ROUTER_PORT, local_file]
            result = subprocess.run(send_cmd, capture_output=True, text=True)
            
            combined_out = result.stdout + result.stderr
            if "Received Store Response (Success)" in combined_out:
                logger.info(f"SUCCESS: DICOM berhasil dikirim ke {ROUTER_AET}")
                cleanup_files(local_file)
                return {"status": "success", "message": "Proses selesai dan berhasil dikirim"}, 200
            else:
                logger.error(f"storescu output: {combined_out}")
                raise Exception("Router menolak file atau tidak ada respon Success")

        except Exception as e:
            msg = str(e)
            logger.error(f"FAILED: {msg}")
            cleanup_files(local_file)
            dicom_ns.abort(500, msg)

@dicom_ns.route('/upload-dcm')
class UploadDicom(Resource):
    @dicom_ns.expect(upload_parser)
    @dicom_ns.doc(description="1. Upload file DCM, 2. Modify Tags, 3. Send to Router")
    def post(self):
        args = upload_parser.parse_args()
        file = args['file']
        patient_id = args['patientid']
        acc_num = args['accesionnum']

        # Simpan file sementara
        temp_filename = f"upload_{file.filename}"
        file.save(temp_filename)
        
        logger.info(f"[UPLOAD] Menerima file: {file.filename} untuk PID: {patient_id}, ACC: {acc_num}")

        try:
            # 1. dcmodify (Edit Tag DICOM)
            logger.info(f"[STEP 1] Modifikasi metadata file upload...")
            modify_cmd = [
                "dcmodify", "--ignore-errors",
                "-i", f"(0010,0020)={patient_id}",
                "-i", f"(0008,0050)={acc_num}",
                temp_filename
            ]
            subprocess.run(modify_cmd, check=True, capture_output=True)
            logger.info("dcmodify berhasil dieksekusi")

            # 2. storescu (Kirim ke Router)
            logger.info(f"[STEP 2] Mengirim {temp_filename} ke {ROUTER_IP}...")
            send_cmd = [
                "storescu", "-v", 
                "-aec", ROUTER_AET, 
                ROUTER_IP, ROUTER_PORT, 
                temp_filename
            ]
            result = subprocess.run(send_cmd, capture_output=True, text=True)
            
            # 3. Validasi Response
            combined_log = result.stdout + result.stderr
            if "Received Store Response (Success)" in combined_log:
                logger.info(f"SUCCESS: Upload & Send Berhasil untuk ACC: {acc_num}")
                cleanup_files(temp_filename)
                return {
                    "status": "success",
                    "message": "File diupload, dimodifikasi, dan dikirim",
                    "accession": acc_num
                }, 200
            else:
                logger.error(f"storescu output: {combined_log}")
                raise Exception("Router menolak koneksi atau tidak memberikan respon success")

        except Exception as e:
            logger.error(f"FAILED: Gagal memproses upload: {str(e)}")
            cleanup_files(temp_filename)
            dicom_ns.abort(500, str(e))


# --- API 3: DIRECT SEND ---
@dicom_ns.route('/direct-dcm')
class DirectDicom(Resource):
    @dicom_ns.expect(direct_model)
    def post(self):
        data = dicom_ns.payload
        study_uid = data.get('study')
        local_file = f"direct_{study_uid}.dcm"
        
        logger.info(f"[DIRECT] Memulai proses Direct Send: {study_uid}")

        try:
            # 1. Ambil Metadata (Gunakan URL yang sudah Anda tes di terminal)
            meta_url = f"{DCM4CHEE_URL}/rs/studies/{study_uid}/metadata"
            meta_resp = requests.get(meta_url, timeout=15)
            meta_resp.raise_for_status()
            metadata = meta_resp.json()
            
            # Ambil UID yang diperlukan
            series_uid = metadata[0]["0020000E"]["Value"][0]
            sop_uid = metadata[0]["00080018"]["Value"][0]

            # 2. Download File via WADO
            wado_url = f"{DCM4CHEE_URL}/wado"
            params = {
                "requestType": "WADO",
                "studyUID": study_uid,
                "seriesUID": series_uid,
                "objectUID": sop_uid,
                "contentType": "application/dicom"
            }
            img_resp = requests.get(wado_url, params=params, stream=True)
            img_resp.raise_for_status()
            
            with open(local_file, 'wb') as f:
                for chunk in img_resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"File berhasil diunduh: {local_file} (Size: {os.path.getsize(local_file)} bytes)")

            # 3. StoreSCU (Gunakan flag yang didukung dcmtk v3.6.7)
            # Kita gunakan --propose-lossless untuk keamanan transfer syntax
            send_cmd = [
                "storescu", "-v", 
                "--propose-lossless", 
                "-aec", ROUTER_AET, 
                ROUTER_IP, ROUTER_PORT, 
                local_file
            ]
            
            result = subprocess.run(send_cmd, capture_output=True, text=True)
            combined_log = result.stdout + result.stderr
            
            # Cek apakah respon mengandung kata 'Success'
            if "Received Store Response (Success)" in combined_log:
                logger.info(f"SUCCESS: Direct Send {study_uid} Berhasil!")
                cleanup_files(local_file)
                return {"status": "success", "message": "Direct Send Berhasil"}, 200
            else:
                # Jika ditolak karena duplikasi, log akan mencatatnya
                logger.error(f"ROUTER REJECTED: {combined_log}")
                raise Exception("Router menolak file (Cek kemungkinan duplikasi UID atau Koneksi)")

        except Exception as e:
            logger.error(f"FAILED: {str(e)}")
            cleanup_files(local_file)
            dicom_ns.abort(500, str(e))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)