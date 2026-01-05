## FLASK DCM4CHE

### 1. API SPEC


| Fitur | API 1: Send from Server (DCM4CHEE) | API 2: Upload & Send (Local File) |
|-------|-----------------------------------|-----------------------------------|
| Endpoint | POST /dicom/send-dcm | POST /dicom/upload-dcm |
| Metode | POST | POST |
| Content-Type | application/json | multipart/form-data |
| Deskripsi | Mengambil file dari server dcm4chee berdasarkan UID (dcm4chee api), mengedit (dcmtk), dan mengirim ke router (dcmtk). | Menerima file .dcm dari komputer user, mengedit (dcmtk), dan mengirim ke router (dcmtk). |
| Parameter Utama | study, patientid, accesionnum | file (binary), patientid, accesionnum |
| Proses Internal | HTTP GET (WADO) → dcmodify → storescu | File Save → dcmodify → storescu |
| Pembersihan | Hapus file .dcm & .bak setelah kirim | Hapus file .dcm & .bak setelah kirim |

```
API 3

POST /api/dicom/direct-dcm	{ "study": "UID" }	

Relay murni: Download dari server PACS DCM4CHE langsung tembak ke dicomrouter.

```

dcm4chee >> dcmtk >> dicom router
Kelebihan :
- tidak perlu settings erver dcm4chee mendaftarkan dicomrouter sebagai modality
- mudah diimplemantasikan dan ringan hanya memanfaatkan dcmtk tool

Kekurangan sistem ini :
- hasil gambar yang dikirimkan ke dicom router status berhasil/ tidak berhasil, hanya menunjukkan keberhasilan kirim ke dicom router bukan menunjukkan langsung succes kirim satu sehat
- jadi perlu di cek ke log dicom router succes kirim ke satu sehat atau tidaknya

### 2. Pendahuluan


- Sudah punya server PACS dengan DCM4CHE

```
PASTIKAN 3 API INI TERSEDIA DAN BISA DIAKSES 

1. API DCM4CHE melihat metadata dari server pacs
http://192.10.10.23:8081/dcm4chee-arc/aets/DCM4CHEE/rs/studies/1.3.46.670589.30.39.0.1.966169802732.1695243280236.1/metadata

2. API DCM4CHE download file dcm dari server pacs de file lokal
http://192.10.10.23:8081/dcm4chee-arc/aets/DCM4CHEE/wado?requestType=WADO&studyUID=1.3.46.670589.30.39.0.1.966169802732.1695243280236.1&seriesUID=1.3.46.670589.30.39.0.1.966169802732.1695243642250.1&objectUID=1.3.46.670589.30.39.0.1.966169802732.1695243642379.1&contentType=application/dicom

3. API DCM4CHE download file dcm dari server pacs ke file lokal dengan nama file
curl -X GET "http://192.10.10.23:8081/dcm4chee-arc/aets/DCM4CHEE/wado?requestType=WADO&studyUID=1.3.46.670589.30.39.0.1.966169802732.1695243280236.1&seriesUID=1.3.46.670589.30.39.0.1.966169802732.1695243642250.1&objectUID=1.3.46.670589.30.39.0.1.966169802732.1695243642379.1&contentType=application/dicom" \ 
-o gambar_pasien.dcm   

```
- Sudah install dicom router docker 

```
mkdir dicom-router 
cd dicom-router 
nano docker-compose.yml 
```
```yml
services: 
  dicom-router: 
    image: registry.dto.kemkes.go.id/pub/dicom-router:latest 
    container_name: dicom-router 
    restart: always 
    ports: 
      - "11112:11112"   # DICOM port router 
      - "8080:8080"     # Web UI router 
    environment: 
      AE_TITLE: DCMROUTER 
      ORG_ID: "10009999" 
      CLIENT: "Gzn7Yj---------------" 
      SECRET: "fbPy8S---------------" 
      WEBHOOK_URL: "https://api-satusehat.kemkes.go.id" 
      WEBHOOK_USER: "youruser" 
      WEBHOOK_PASSWORD: "yourpass" 
      URL: "https://api-satusehat.kemkes.go.id" 
    networks: 
      - dicom-network 
 
networks: 
  dicom-network: 
    driver: bridge 
```
dicom router tidak perlu di daftarkan ke server pacs dcm4chee

```
docker compose up -d 
docker ps -a 
docker logs dicom-router | head -n 50 
docker logs -f dicom-router 
sudo netstat -tulpn | grep 11112 
```
PASTIKAN server dcm router berjalan
```
docker ps --filter "name=dicom-router"

CONTAINER ID   IMAGE                                               COMMAND                CREATED      STATUS      PORTS                                                                                          NAMES
3e7b0312d7d4   registry.dto.kemkes.go.id/pub/dicom-router:latest   "/app/entrypoint.sh"   2 days ago   Up 2 days   0.0.0.0:8080->8080/tcp, [::]:8080->8080/tcp, 0.0.0.0:11112->11112/tcp, [::]:11112->11112/tcp   dicom-router

```
- Sudah install DCMTK dalam OS

```
Install dcmtk
sudo apt install dcmtk -y 

Melihat patient id dan Acession Number
dcmdump gambar_pasien.dcm | grep -E "(0010,0020)|(0008,0050)"

Modify patient id dan Acession Number
dcmodify --ignore-errors \ 
-i "(0010,0020)=P00001349322" \ 
-i "(0008,0050)=202512300002" \ 
gambar_pasien.dcm 

Kirim file dcm ke dicom router
storescu -aec -v DCMROUTER 192.10.10.28 11112 ambar_pasien.dcm 

```
Ujicoba bisa menggunakan file dcm dari inet kemudian dicoba

https://www.rubomedical.com/dicom_files/dicom_viewer_0003.zip

### SATUSEHAT 

1. ENCOUNTER 
2. SERVICE REQUEST >> PATIENT ID, ACCESION NUMBER
- pasient id tidak diubah data tetap bisa dikirim ke satusehat
- mandatory accesion number wajib dikirim service request sama dengan accesion number pada gambar dicom

### 3. Persiapan pembuatan API

```py

# Update sistem
sudo apt update && sudo apt upgrade -y

# Install python3-venv jika belum ada
sudo apt install python3-venv -y

# Buat virtual environment
python3 -m venv venv

# Aktifkan virtual environment
source venv/bin/activate # Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install package yang diperlukan
pip install flask flask-restx requests werkzeug

```

### 4. Struktur File Proyek
```Plaintext

dicom-gateway/
├── app.py              # Script utama Flask (API & Logic)
├── requirements.txt    # Daftar library Python yang dibutuhkan
├── app_dicom.log       # File log (akan terbuat otomatis, maks 1000 baris)
└── uploads/            # (Opsional) 

```

### 5. Isi requirements.txt

```Plaintext
flask
flask-restx
requests
werkzeug
```

```Bash
pip install -r requirements.txt
```

### 6. app.py ujicoba API 1: Send from Server (DCM4CHEE)

```py
from flask import Flask, request, jsonify 
import requests 
import subprocess 
import os 
 
app = Flask(__name__) 
 
# Konfigurasi 
DCM4CHEE_URL = "http://192.10.10.23:8081/dcm4chee-arc/aets/DCM4CHEE" 
ROUTER_IP = "192.10.10.28" 
ROUTER_PORT = "11112" 
ROUTER_AET = "DCMROUTER" 
 
def cleanup_files(filename): 
    """Menghapus file .dcm dan file cadangan .bak dari dcmodify""" 
    for ext in ["", ".bak"]: 
        path = f"{filename}{ext}" 
        if os.path.exists(path): 
            os.remove(path) 
 
@app.route('/send-dcm', methods=['POST']) 
def send_dicom(): 
    data = request.get_json() 
    study_uid = data.get('study') 
    patient_id = data.get('patientid') 
    accession_num = data.get('accesionnum') 
 
    if not all([study_uid, patient_id, accession_num]): 
        return jsonify({"error": "Data study, patientid, dan accesionnum wajib diisi"}), 400 
 
    local_file = f"temp_{study_uid}.dcm" 
 
    try: 
        # 1. Ambil Metadata (Cari Series & SOP Instance UID) 
        meta_url = f"{DCM4CHEE_URL}/rs/studies/{study_uid}/metadata" 
        meta_resp = requests.get(meta_url, timeout=10) 
        meta_resp.raise_for_status() 
        metadata = meta_resp.json() 
 
        # Ambil instance pertama 
        series_uid = metadata[0]["0020000E"]["Value"][0] 
        sop_uid = metadata[0]["00080018"]["Value"][0] 
 
        # 2. Download DICOM via WADO 
        wado_url = f"{DCM4CHEE_URL}/wado" 
        params = { 
            "requestType": "WADO", 
            "studyUID": study_uid, 
            "seriesUID": series_uid, 
            "objectUID": sop_uid, 
            "contentType": "application/dicom" 
        } 
         
        img_resp = requests.get(wado_url, params=params, stream=True) 
        with open(local_file, 'wb') as f: 
            for chunk in img_resp.iter_content(chunk_size=8192): 
                f.write(chunk) 
 
        # 4. Edit Metadata dengan dcmodify (Langkah yang sudah berhasil di Pi Anda) 
        modify_cmd = [ 
            "dcmodify", "--ignore-errors", 
            "-i", f"(0010,0020)={patient_id}", 
            "-i", f"(0008,0050)={accession_num}", 
            local_file 
        ] 
        subprocess.run(modify_cmd, check=True, capture_output=True) 
 
        # 6. Kirim ke Router dengan storescu -v (Verbose) 
        send_cmd = [ 
            "storescu", "-v",  
            "-aec", ROUTER_AET,  
            ROUTER_IP, ROUTER_PORT,  
            local_file 
        ] 
         
        # Capture stderr karena log verbose storescu biasanya keluar di stderr 
        result = subprocess.run(send_cmd, capture_output=True, text=True) 
         
        combined_output = result.stdout + result.stderr 
 
        # 7. Validasi Akurat: Cek string "Success" dalam output 
        if "Received Store Response (Success)" in combined_output: 
            cleanup_files(local_file) 
            return jsonify({ 
                "status": "success", 
                "message": f"DICOM {accession_num} terkirim dan diverifikasi", 
                "study_uid": study_uid 
            }), 200 
        else: 
            raise Exception(f"Router menerima koneksi tapi gagal simpan: {combined_output}") 
 
    except subprocess.CalledProcessError as e: 
        cleanup_files(local_file) 
        return jsonify({"status": "error", "step": "CLI Fail", "detail": str(e.stderr)}), 500 
    except Exception as e: 
        cleanup_files(local_file) 
        return jsonify({"status": "error", "message": str(e)}), 500 
 
if __name__ == '__main__': 
    app.run(host='0.0.0.0', port=5000) 
 
```

```
mejalankan server :
python app.py

coba dengan curl
curl -X POST http://localhost:5000/send-dcm \ 
-H "Content-Type: application/json" \ 
-d '{ 
  "study": "1.3.46.670589.30.39.0.1.966169802732.1695243280236.1", 
  "patientid": "P00001349322", 
  "accesionnum": "202512300002" 
}' 

contoh
curl -X POST http://192.168.30.14:5000/send-dcm -H "Content-Type: application/json" -d '{"study": "1.3.46.670589.30.39.0.1.966169802732.1695243280236.1", "patientid": "P00001349322", "accesionnum": "202512300002"}'
hasil
{"message":"DICOM 202512300002 terkirim dan diverifikasi","status":"success","study_uid":"1.3.46.670589.30.39.0.1.966169802732.1695243280236.1"}
```

### 7. app.py API 1: Send from Server (DCM4CHEE) dengan swagger ui

```py 
# pip install flask-restx
from flask import Flask
from flask_restx import Api, Resource, Namespace, fields
import requests
import subprocess
import os

app = Flask(__name__)
api = Api(app, version='1.0', title='DICOM Sender API',
          description='API untuk manipulasi metadata DICOM dan pengiriman ke Router')

# Konfigurasi
DCM4CHEE_URL = "http://192.10.10.23:8081/dcm4chee-arc/aets/DCM4CHEE"
ROUTER_IP = "192.10.10.28"
ROUTER_PORT = "11112"
ROUTER_AET = "DCMROUTER"

# Namespace
ns = Namespace('dicom', description='Operasi pengiriman gambar DICOM')
api.add_namespace(ns)

# Model untuk Dokumentasi Swagger
dicom_model = ns.model('DicomSend', {
    'study': fields.String(required=True, description='Study Instance UID', example='1.3.46.670589.30.39.0.1.966169802732.1695243280236.1'),
    'patientid': fields.String(required=True, description='ID Pasien Baru', example='P00001349322'),
    'accesionnum': fields.String(required=True, description='Accession Number Baru', example='202512300002')
})

def cleanup_files(filename):
    for ext in ["", ".bak"]:
        path = f"{filename}{ext}"
        if os.path.exists(path):
            os.remove(path)

@ns.route('/send-dcm')
class SendDicom(Resource):
    @ns.expect(dicom_model)
    @ns.response(200, 'Success')
    @ns.response(400, 'Validation Error')
    @ns.response(500, 'Internal Server Error')
    def post(self):
        """Ambil, Edit, dan Kirim gambar DICOM"""
        data = ns.payload
        study_uid = data.get('study')
        patient_id = data.get('patientid')
        accession_num = data.get('accesionnum')

        local_file = f"temp_{study_uid}.dcm"

        try:
            # 1. Ambil Metadata
            meta_url = f"{DCM4CHEE_URL}/rs/studies/{study_uid}/metadata"
            meta_resp = requests.get(meta_url, timeout=10)
            meta_resp.raise_for_status()
            metadata = meta_resp.json()

            series_uid = metadata[0]["0020000E"]["Value"][0]
            sop_uid = metadata[0]["00080018"]["Value"][0]

            # 2. Download DICOM
            wado_url = f"{DCM4CHEE_URL}/wado"
            params = {
                "requestType": "WADO",
                "studyUID": study_uid,
                "seriesUID": series_uid,
                "objectUID": sop_uid,
                "contentType": "application/dicom"
            }
            
            img_resp = requests.get(wado_url, params=params, stream=True)
            with open(local_file, 'wb') as f:
                for chunk in img_resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            # 4. Edit Metadata (dcmodify)
            modify_cmd = [
                "dcmodify", "--ignore-errors",
                "-i", f"(0010,0020)={patient_id}",
                "-i", f"(0008,0050)={accession_num}",
                local_file
            ]
            subprocess.run(modify_cmd, check=True, capture_output=True)

            # 6. Kirim ke Router (storescu)
            send_cmd = [
                "storescu", "-v", 
                "-aec", ROUTER_AET, 
                ROUTER_IP, ROUTER_PORT, 
                local_file
            ]
            result = subprocess.run(send_cmd, capture_output=True, text=True)
            combined_log = result.stdout + result.stderr

            # 7. Validasi
            if "Received Store Response (Success)" in combined_log:
                cleanup_files(local_file)
                return {
                    "status": "success",
                    "message": "DICOM terkirim dan diverifikasi",
                    "accession": accession_num
                }, 200
            else:
                raise Exception(f"StoreSCU gagal: {combined_log}")

        except Exception as e:
            cleanup_files(local_file)
            ns.abort(500, str(e))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

### 8. app.py dengan logger

```py
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_restx import Api, Resource, Namespace, fields
import requests
import subprocess
import os

app = Flask(__name__)

# --- KONFIGURASI LOGGER ---
# Membatasi file log sekitar 150KB (asumsi ~1000-1200 baris log standar)
log_filename = 'app_dicom.log'
log_handler = RotatingFileHandler(log_filename, maxBytes=150000, backupCount=1)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)

logger = logging.getLogger('DicomLogger')
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# --- KONFIGURASI API ---
api = Api(app, version='1.0', title='DICOM Sender API',
          description='API dengan Logging Terbatas (Rotating)')

DCM4CHEE_URL = "http://192.10.10.23:8081/dcm4chee-arc/aets/DCM4CHEE"
ROUTER_IP = "192.10.10.28"
ROUTER_PORT = "11112"
ROUTER_AET = "DCMROUTER"

ns = Namespace('dicom', description='Operasi DICOM ke Router')
api.add_namespace(ns)

dicom_model = ns.model('DicomSend', {
    'study': fields.String(required=True, example='1.3.46...'),
    'patientid': fields.String(required=True, example='P00001349322'),
    'accesionnum': fields.String(required=True, example='202512300002')
})

def cleanup_files(filename):
    for ext in ["", ".bak"]:
        path = f"{filename}{ext}"
        if os.path.exists(path):
            os.remove(path)

@ns.route('/send-dcm')
class SendDicom(Resource):
    @ns.expect(dicom_model)
    def post(self):
        data = ns.payload
        study_uid = data.get('study')
        patient_id = data.get('patientid')
        acc_num = data.get('accesionnum')

        local_file = f"temp_{study_uid}.dcm"
        logger.info(f"Memproses Study: {study_uid} untuk PatientID: {patient_id}")

        try:
            # 1. Ambil Metadata
            meta_url = f"{DCM4CHEE_URL}/rs/studies/{study_uid}/metadata"
            meta_resp = requests.get(meta_url, timeout=10)
            meta_resp.raise_for_status()
            metadata = meta_resp.json()

            series_uid = metadata[0]["0020000E"]["Value"][0]
            sop_uid = metadata[0]["00080018"]["Value"][0]

            # 2. Download DICOM
            wado_url = f"{DCM4CHEE_URL}/wado"
            params = {
                "requestType": "WADO", "studyUID": study_uid,
                "seriesUID": series_uid, "objectUID": sop_uid,
                "contentType": "application/dicom"
            }
            img_resp = requests.get(wado_url, params=params, stream=True)
            with open(local_file, 'wb') as f:
                for chunk in img_resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            # 4. dcmodify (Sesuai cara Anda di Raspberry Pi)
            modify_cmd = [
                "dcmodify", "--ignore-errors",
                "-i", f"(0010,0020)={patient_id}",
                "-i", f"(0008,0050)={acc_num}",
                local_file
            ]
            subprocess.run(modify_cmd, check=True, capture_output=True)
            logger.info(f"Metadata berhasil diubah: {acc_num}")

            # 6. storescu (Kirim & Cek Success)
            send_cmd = ["storescu", "-v", "-aec", ROUTER_AET, ROUTER_IP, ROUTER_PORT, local_file]
            result = subprocess.run(send_cmd, capture_output=True, text=True)
            
            if "Received Store Response (Success)" in (result.stdout + result.stderr):
                logger.info(f"Kirim Berhasil: {acc_num} ke {ROUTER_IP}")
                cleanup_files(local_file)
                return {"status": "success", "detail": "DICOM Sent Successfully"}, 200
            else:
                logger.error(f"Kirim Gagal (No Success Response): {result.stderr}")
                raise Exception("Router tidak memberikan respon Success")

        except Exception as e:
            logger.error(f"Terjadi Error: {str(e)}")
            cleanup_files(local_file)
            ns.abort(500, str(e))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

```

### 9. app.py dengan render html
```
dicom-gateway-docker/
├── app/
│   ├── app.py              # Skrip Flask lengkap Anda
│   ├── templates/
│   │   └── dcmpage.html    # File UI Dashboard
│   └── requirements.txt    # Library Python
├── Dockerfile              # Instruksi pembuatan image
└── docker-compose.yml      # Konfigurasi orkestrasi Docker
```

```py
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, jsonify
from flask_restx import Api, Resource, Namespace, fields
import requests
import subprocess
import os

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```
```html
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DICOM Gateway Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        :root {
            --bg-color: #f4f7f6;
            --console-bg: #1e1e1e;
            --console-text: #00ff00;
        }

        body { 
            background-color: var(--bg-color); 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        .navbar-brand { font-weight: 700; letter-spacing: 1px; }

        .card { 
            border-radius: 12px; 
            border: none; 
            overflow: hidden;
        }

        .card-header { 
            background-color: #fff !important; 
            font-weight: bold; 
            border-bottom: 1px solid #eee;
            padding: 1rem 1.25rem;
        }

        /* Log Console Style */
        .log-container {
            background: var(--console-bg);
            color: var(--console-text);
            padding: 15px;
            height: 400px;
            overflow-y: auto;
            font-family: 'Courier New', Courier, monospace;
            font-size: 13px;
            border-radius: 8px;
            border: 2px solid #333;
            box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
        }

        .log-entry { 
            margin-bottom: 5px; 
            border-bottom: 1px solid #2a2a2a; 
            padding-bottom: 2px;
            line-height: 1.4;
        }

        .timestamp { color: #888; font-size: 11px; margin-right: 8px; }
        
        /* Tab Styling */
        .nav-tabs .nav-link { color: #555; font-weight: 500; border: none; }
        .nav-tabs .nav-link.active { 
            color: #0d6efd; 
            border-bottom: 3px solid #0d6efd; 
            background: transparent;
        }

        /* Custom Scrollbar for Log */
        .log-container::-webkit-scrollbar { width: 8px; }
        .log-container::-webkit-scrollbar-track { background: #121212; }
        .log-container::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
    </style>
</head>
<body>

<nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4 shadow">
    <div class="container">
        <a class="navbar-brand" href="#">
            <i class="fa-solid fa-microchip me-2 text-info"></i>DICOM GATEWAY 
            <span class="badge bg-secondary ms-2" style="font-size: 0.6rem;">RASPBERRY PI v1.0</span>
        </a>
        <div class="navbar-nav ms-auto">
            <a class="nav-link" href="/api/docs" target="_blank"><i class="fa-solid fa-book me-1"></i> Swagger API</a>
        </div>
    </div>
</nav>

<div class="container">
    <div class="row g-4">
        
        <div class="col-lg-5">
            <div class="card shadow-sm">
                <div class="card-header">
                    <i class="fa-solid fa-circle-info me-2 text-primary"></i>Input Study DICOM
                </div>
                <div class="card-body p-4">
                    <form id="formSend">
                        <div class="mb-4">
                            <label class="form-label fw-bold small">Study Instance UID</label>
                            <div class="input-group">
                                <span class="input-group-text bg-light"><i class="fa-solid fa-fingerprint"></i></span>
                                <input type="text" class="form-control" id="send-study" placeholder="1.3.46.670589..." required>
                            </div>
                            <div class="form-text">UID unik dari server DCM4CHEE.</div>
                        </div>

                        <div class="mb-3">
                            <label class="form-label fw-bold small">Patient ID Baru</label>
                            <input type="text" class="form-control" id="send-pid" placeholder="Contoh: P12345" required>
                        </div>

                        <div class="mb-4">
                            <label class="form-label fw-bold small">Accession Number Baru</label>
                            <input type="text" class="form-control" id="send-acc" placeholder="Contoh: 202600001" required>
                        </div>

                        <button type="submit" id="btnSubmit" class="btn btn-primary w-100 py-2 fw-bold shadow-sm">
                            <i class="fa-solid fa-paper-plane me-2"></i>EKSEKUSI PROSES
                        </button>
                    </form>
                </div>
                <div class="card-footer bg-light border-0 py-3">
                    <small class="text-muted">
                        <i class="fa-solid fa-triangle-exclamation me-1"></i> 
                        Pastikan Router tujuan (192.10.10.28) dalam posisi Online.
                    </small>
                </div>
            </div>
        </div>

        <div class="col-lg-7">
            <div class="card shadow-sm">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <span><i class="fa-solid fa-terminal me-2 text-success"></i>Process Console</span>
                    <button class="btn btn-sm btn-outline-danger border-0" onclick="clearLog()">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </div>
                <div class="card-body">
                    <div class="log-container" id="logConsole">
                        <div class="log-entry text-muted">>> System initialized. Waiting for command...</div>
                    </div>
                </div>
            </div>
        </div>

    </div>
</div>

<div class="modal fade" id="loadingModal" data-bs-backdrop="static" data-bs-keyboard="false" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content border-0 bg-transparent">
            <div class="card w-100 p-5 text-center border-0 shadow-lg">
                <div class="spinner-border text-primary mx-auto mb-4" style="width: 3.5rem; height: 3.5rem; border-width: 0.25em;" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <h4 class="mb-2">Sedang Memproses...</h4>
                <p class="text-muted mb-0">Sistem sedang Fetching, Modifying, dan Sending file DICOM.</p>
                <p class="text-danger small mt-2 fw-bold">Mohon jangan tutup atau refresh halaman ini.</p>
            </div>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

<script>
    // Inisialisasi Element & Modal
    const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    const logConsole = document.getElementById('logConsole');
    const formSend = document.getElementById('formSend');
    const btnSubmit = document.getElementById('btnSubmit');

    // Fungsi Tambah Log ke Konsol
    function addLog(message, type = 'info') {
        const time = new Date().toLocaleTimeString('id-ID');
        let color = "#00ff00"; // default hijau (info/success)
        
        if (type === 'error') color = "#ff4d4d"; // merah
        if (type === 'warning') color = "#ffcc00"; // kuning
        
        const entry = document.createElement('div');
        entry.className = "log-entry";
        entry.style.color = color;
        entry.innerHTML = `<span class="timestamp">[${time}]</span> <span class="fw-bold">>></span> ${message}`;
        
        logConsole.appendChild(entry);
        
        // Auto scroll ke bawah
        logConsole.scrollTop = logConsole.scrollHeight;
    }

    // Fungsi Clear Log
    function clearLog() {
        logConsole.innerHTML = '<div class="log-entry text-muted">>> Console cleared.</div>';
    }

    // Event Handler Form Submit
    formSend.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Ambil Data
        const payload = {
            study: document.getElementById('send-study').value.trim(),
            patientid: document.getElementById('send-pid').value.trim(),
            accesionnum: document.getElementById('send-acc').value.trim()
        };

        // UI State: Show Loading
        loadingModal.show();
        btnSubmit.disabled = true;
        addLog(`MEMULAI PROSES: Study ${payload.study}`, 'info');

        try {
            // Kirim Request ke API Flask-RestX
            const response = await fetch('/api/dicom/send-dcm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (response.ok) {
                addLog(`BERHASIL: DICOM Study ${payload.study} telah dikirim ke Router.`, 'info');
                addLog(`Detail: ${result.message}`, 'info');
                // Reset form jika sukses
                formSend.reset();
            } else {
                // Handle error dari Backend (400/500)
                const errorMsg = result.message || "Gagal memproses data.";
                addLog(`ERROR: ${errorMsg}`, 'error');
            }

        } catch (err) {
            // Handle error koneksi (network error)
            addLog(`KONEKSI GAGAL: Tidak dapat terhubung ke server backend Flask.`, 'error');
            console.error(err);
        } finally {
            // Sembunyikan Loading & Enable Tombol
            setTimeout(() => {
                loadingModal.hide();
                btnSubmit.disabled = false;
            }, 800);
        }
    });
</script>

</body>
</html>
```


### 10. app,py dengan tambahan api uploud file 
```py
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

```
templates/dcmpage.html

```html
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DICOM Gateway Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        :root {
            --bg-color: #f4f7f6;
            --console-bg: #1e1e1e;
            --console-text: #00ff00;
        }

        body { background-color: var(--bg-color); font-family: 'Segoe UI', sans-serif; }
        .card { border-radius: 12px; border: none; shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .card-header { background: #fff !important; font-weight: bold; border-bottom: 1px solid #eee; }
        
        /* Log Console Style */
        .log-container {
            background: var(--console-bg);
            color: var(--console-text);
            padding: 15px;
            height: 480px;
            overflow-y: auto;
            font-family: 'Courier New', Courier, monospace;
            font-size: 13px;
            border-radius: 8px;
            border: 2px solid #333;
        }
        .log-entry { margin-bottom: 5px; border-bottom: 1px solid #2a2a2a; padding-bottom: 2px; }
        .timestamp { color: #888; font-size: 11px; margin-right: 8px; }
        
        /* Tab Styling */
        .nav-tabs .nav-link { color: #555; font-weight: 500; border: none; }
        .nav-tabs .nav-link.active { color: #0d6efd; border-bottom: 3px solid #0d6efd; background: transparent; }
    </style>
</head>
<body>

<nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4 shadow">
    <div class="container">
        <a class="navbar-brand" href="#"><i class="fa-solid fa-microchip me-2 text-info"></i>DICOM Gateway <span class="badge bg-secondary ms-2">RPi v1.0</span></a>
        <div class="navbar-nav ms-auto">
            <a class="nav-link" href="/api/docs" target="_blank"><i class="fa-solid fa-book me-1"></i> API Docs</a>
        </div>
    </div>
</nav>

<div class="container">
    <div class="row g-4">
        
        <div class="col-lg-6">
            <div class="card shadow-sm">
                <div class="card-header py-3">
                    <ul class="nav nav-tabs card-header-tabs" id="dicomTab" role="tablist">
                        <li class="nav-item">
                            <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#tab-fetch"><i class="fa-solid fa-sync me-1"></i> Fetch & Send</button>
                        </li>
                        <li class="nav-item">
                            <button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-upload"><i class="fa-solid fa-upload me-1"></i> Manual Upload</button>
                        </li>
                    </ul>
                </div>
                
                <div class="card-body p-4">
                    <div class="tab-content">
                        
                        <div class="tab-pane fade show active" id="tab-fetch">
                            <form id="formFetch">
                                <div class="mb-3">
                                    <label class="form-label small fw-bold">Study Instance UID (DCM4CHEE)</label>
                                    <input type="text" class="form-control" id="fetch-study" placeholder="1.3.46.67..." required>
                                </div>
                                <div class="row mb-3">
                                    <div class="col">
                                        <label class="form-label small fw-bold">Patient ID Baru</label>
                                        <input type="text" class="form-control" id="fetch-pid" placeholder="P-001" required>
                                    </div>
                                    <div class="col">
                                        <label class="form-label small fw-bold">Accession No. Baru</label>
                                        <input type="text" class="form-control" id="fetch-acc" placeholder="ACC-001" required>
                                    </div>
                                </div>
                                <button type="submit" class="btn btn-primary w-100 fw-bold">PROSES & KIRIM</button>
                            </form>
                        </div>

                        <div class="tab-pane fade" id="tab-upload">
                            <form id="formUpload">
                                <div class="mb-3">
                                    <label class="form-label small fw-bold">File DICOM (.dcm)</label>
                                    <input type="file" class="form-control" id="upload-file" accept=".dcm" required>
                                </div>
                                <div class="row mb-3">
                                    <div class="col">
                                        <label class="form-label small fw-bold">Patient ID Baru</label>
                                        <input type="text" class="form-control" id="upload-pid" placeholder="P-001" required>
                                    </div>
                                    <div class="col">
                                        <label class="form-label small fw-bold">Accession No. Baru</label>
                                        <input type="text" class="form-control" id="upload-acc" placeholder="ACC-001" required>
                                    </div>
                                </div>
                                <button type="submit" class="btn btn-success w-100 fw-bold">UPLOAD & KIRIM</button>
                            </form>
                        </div>

                    </div>
                </div>
            </div>
        </div>

        <div class="col-lg-6">
            <div class="card shadow-sm">
                <div class="card-header d-flex justify-content-between align-items-center py-3">
                    <span><i class="fa-solid fa-terminal me-2 text-success"></i>Process Console</span>
                    <button class="btn btn-sm btn-outline-danger border-0" onclick="document.getElementById('logConsole').innerHTML='' ">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
                <div class="card-body">
                    <div class="log-container" id="logConsole">
                        <div class="log-entry text-muted">>> System ready. Menunggu input...</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="modal fade" id="loadingModal" data-bs-backdrop="static" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content border-0 bg-transparent">
            <div class="card w-100 p-4 text-center border-0 shadow-lg">
                <div class="spinner-border text-primary mx-auto mb-3" style="width: 3rem; height: 3rem;" role="status"></div>
                <h5 class="mb-1">Sedang Memproses DICOM...</h5>
                <p class="text-muted small mb-0">Mohon tunggu, sistem sedang menjalankan tugas.</p>
            </div>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

<script>
    const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    const logConsole = document.getElementById('logConsole');

    function addLog(message, type = 'info') {
        const time = new Date().toLocaleTimeString('id-ID');
        let color = "#00ff00"; 
        if(type === 'error') color = "#ff4d4d";
        if(type === 'warning') color = "#ffcc00";

        const entry = document.createElement('div');
        entry.className = "log-entry";
        entry.style.color = color;
        entry.innerHTML = `<span class="timestamp">[${time}]</span> >> ${message}`;
        logConsole.appendChild(entry);
        logConsole.scrollTop = logConsole.scrollHeight;
    }

    // --- LOGIKA API 1: FETCH & SEND ---
    document.getElementById('formFetch').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            study: document.getElementById('fetch-study').value,
            patientid: document.getElementById('fetch-pid').value,
            accesionnum: document.getElementById('fetch-acc').value
        };

        loadingModal.show();
        addLog(`Memulai Fetch dari DCM4CHEE: ${payload.study}`);

        try {
            const resp = await fetch('/api/dicom/send-dcm', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const res = await resp.json();
            if (resp.ok) {
                addLog(`BERHASIL: ${res.message}`, 'info');
            } else {
                addLog(`GAGAL: ${res.message || 'Error Server'}`, 'error');
            }
        } catch (err) {
            addLog(`ERROR KONEKSI: ${err.message}`, 'error');
        } finally {
            loadingModal.hide();
        }
    });

    // --- LOGIKA API 2: MANUAL UPLOAD ---
    document.getElementById('formUpload').addEventListener('submit', async (e) => {
        e.preventDefault();
        const fileInput = document.getElementById('upload-file');
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('patientid', document.getElementById('upload-pid').value);
        formData.append('accesionnum', document.getElementById('upload-acc').value);

        loadingModal.show();
        addLog(`Mengunggah file: ${fileInput.files[0].name}`);

        try {
            const resp = await fetch('/api/dicom/upload-dcm', {
                method: 'POST',
                body: formData
            });
            const res = await resp.json();
            if (resp.ok) {
                addLog(`BERHASIL: ${res.message} (ACC: ${res.accession})`, 'info');
                document.getElementById('formUpload').reset();
            } else {
                addLog(`GAGAL: ${res.message || 'Error Server'}`, 'error');
            }
        } catch (err) {
            addLog(`ERROR KONEKSI: ${err.message}`, 'error');
        } finally {
            loadingModal.hide();
        }
    });
</script>

</body>
</html>
```
### 11. app.py dengan direct send dicom 

```py
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
```

```html
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DICOM Gateway Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        :root {
            --bg-color: #f4f7f6;
            --console-bg: #1e1e1e;
            --console-text: #00ff00;
        }

        body { background-color: var(--bg-color); font-family: 'Segoe UI', sans-serif; }
        .card { border-radius: 12px; border: none; shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .card-header { background: #fff !important; font-weight: bold; border-bottom: 1px solid #eee; }
        
        /* Log Console Style */
        .log-container {
            background: var(--console-bg);
            color: var(--console-text);
            padding: 15px;
            height: 480px;
            overflow-y: auto;
            font-family: 'Courier New', Courier, monospace;
            font-size: 13px;
            border-radius: 8px;
            border: 2px solid #333;
        }
        .log-entry { margin-bottom: 5px; border-bottom: 1px solid #2a2a2a; padding-bottom: 2px; }
        .timestamp { color: #888; font-size: 11px; margin-right: 8px; }
        
        /* Tab Styling */
        .nav-tabs .nav-link { color: #555; font-weight: 500; border: none; }
        .nav-tabs .nav-link.active { color: #0d6efd; border-bottom: 3px solid #0d6efd; background: transparent; }
    </style>
</head>
<body>

<nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4 shadow">
    <div class="container">
        <a class="navbar-brand" href="#"><i class="fa-solid fa-microchip me-2 text-info"></i>DICOM Gateway <span class="badge bg-secondary ms-2">RPi v1.0</span></a>
        <div class="navbar-nav ms-auto">
            <a class="nav-link" href="/api/docs" target="_blank"><i class="fa-solid fa-book me-1"></i> API Docs</a>
        </div>
    </div>
</nav>

<div class="container">
    <div class="row g-4">
        
        <div class="col-lg-6">
            <div class="card shadow-sm">
                <div class="card-header py-3">
                    <ul class="nav nav-tabs card-header-tabs" id="dicomTab" role="tablist">
                        <li class="nav-item">
                            <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#tab-fetch"><i class="fa-solid fa-sync me-1"></i> Fetch & Send</button>
                        </li>
                        <li class="nav-item">
                            <button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-upload"><i class="fa-solid fa-upload me-1"></i> Manual Upload</button>
                        </li>
                        <li class="nav-item">
                            <button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-direct"><i class="fa-solid fa-bolt me-1"></i> Direct Send</button>
                        </li>
                    </ul>
                </div>
                
                <div class="card-body p-4">
                    <div class="tab-content">
                        
                        <div class="tab-pane fade show active" id="tab-fetch">
                            <form id="formFetch">
                                <div class="mb-3">
                                    <label class="form-label small fw-bold">Study Instance UID (DCM4CHEE)</label>
                                    <input type="text" class="form-control" id="fetch-study" placeholder="1.3.46.67..." required>
                                </div>
                                <div class="row mb-3">
                                    <div class="col">
                                        <label class="form-label small fw-bold">Patient ID Baru</label>
                                        <input type="text" class="form-control" id="fetch-pid" placeholder="P-001" required>
                                    </div>
                                    <div class="col">
                                        <label class="form-label small fw-bold">Accession No. Baru</label>
                                        <input type="text" class="form-control" id="fetch-acc" placeholder="ACC-001" required>
                                    </div>
                                </div>
                                <button type="submit" class="btn btn-primary w-100 fw-bold">PROSES & KIRIM</button>
                            </form>
                        </div>

                        <div class="tab-pane fade" id="tab-upload">
                            <form id="formUpload">
                                <div class="mb-3">
                                    <label class="form-label small fw-bold">File DICOM (.dcm)</label>
                                    <input type="file" class="form-control" id="upload-file" accept=".dcm" required>
                                </div>
                                <div class="row mb-3">
                                    <div class="col">
                                        <label class="form-label small fw-bold">Patient ID Baru</label>
                                        <input type="text" class="form-control" id="upload-pid" placeholder="P-001" required>
                                    </div>
                                    <div class="col">
                                        <label class="form-label small fw-bold">Accession No. Baru</label>
                                        <input type="text" class="form-control" id="upload-acc" placeholder="ACC-001" required>
                                    </div>
                                </div>
                                <button type="submit" class="btn btn-success w-100 fw-bold">UPLOAD & KIRIM</button>
                            </form>
                        </div>
                        
                        <div class="tab-pane fade" id="tab-direct">
                            <form id="formDirect">
                                <div class="mb-4">
                                    <label class="form-label small fw-bold">Study Instance UID</label>
                                    <input type="text" class="form-control" id="direct-study" placeholder="Kirim data asli tanpa modifikasi..." required>
                                </div>
                                <div class="alert alert-warning py-2 small">
                                    <i class="fa-solid fa-triangle-exclamation me-2"></i>
                                    Perhatian: Data akan dikirim apa adanya sesuai sumber asli (DCM4CHEE).
                                </div>
                                <button type="submit" class="btn btn-warning w-100 fw-bold">KIRIM LANGSUNG</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="col-lg-6">
            <div class="card shadow-sm">
                <div class="card-header d-flex justify-content-between align-items-center py-3">
                    <span><i class="fa-solid fa-terminal me-2 text-success"></i>Process Console</span>
                    <button class="btn btn-sm btn-outline-danger border-0" onclick="document.getElementById('logConsole').innerHTML='' ">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
                <div class="card-body">
                    <div class="log-container" id="logConsole">
                        <div class="log-entry text-muted">>> System ready. Menunggu input...</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="modal fade" id="loadingModal" data-bs-backdrop="static" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content border-0 bg-transparent">
            <div class="card w-100 p-4 text-center border-0 shadow-lg">
                <div class="spinner-border text-primary mx-auto mb-3" style="width: 3rem; height: 3rem;" role="status"></div>
                <h5 class="mb-1">Sedang Memproses DICOM...</h5>
                <p class="text-muted small mb-0">Mohon tunggu, sistem sedang menjalankan tugas.</p>
            </div>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

<script>
    const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    const logConsole = document.getElementById('logConsole');

    function addLog(message, type = 'info') {
        const time = new Date().toLocaleTimeString('id-ID');
        let color = "#00ff00"; 
        if(type === 'error') color = "#ff4d4d";
        if(type === 'warning') color = "#ffcc00";

        const entry = document.createElement('div');
        entry.className = "log-entry";
        entry.style.color = color;
        entry.innerHTML = `<span class="timestamp">[${time}]</span> >> ${message}`;
        logConsole.appendChild(entry);
        logConsole.scrollTop = logConsole.scrollHeight;
    }

    // --- LOGIKA API 1: FETCH & SEND ---
    document.getElementById('formFetch').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            study: document.getElementById('fetch-study').value,
            patientid: document.getElementById('fetch-pid').value,
            accesionnum: document.getElementById('fetch-acc').value
        };

        loadingModal.show();
        addLog(`Memulai Fetch dari DCM4CHEE: ${payload.study}`);

        try {
            const resp = await fetch('/api/dicom/send-dcm', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const res = await resp.json();
            if (resp.ok) {
                addLog(`BERHASIL: ${res.message}`, 'info');
            } else {
                addLog(`GAGAL: ${res.message || 'Error Server'}`, 'error');
            }
        } catch (err) {
            addLog(`ERROR KONEKSI: ${err.message}`, 'error');
        } finally {
            loadingModal.hide();
        }
    });

    // --- LOGIKA API 2: MANUAL UPLOAD ---
    document.getElementById('formUpload').addEventListener('submit', async (e) => {
        e.preventDefault();
        const fileInput = document.getElementById('upload-file');
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('patientid', document.getElementById('upload-pid').value);
        formData.append('accesionnum', document.getElementById('upload-acc').value);

        loadingModal.show();
        addLog(`Mengunggah file: ${fileInput.files[0].name}`);

        try {
            const resp = await fetch('/api/dicom/upload-dcm', {
                method: 'POST',
                body: formData
            });
            const res = await resp.json();
            if (resp.ok) {
                addLog(`BERHASIL: ${res.message} (ACC: ${res.accession})`, 'info');
                document.getElementById('formUpload').reset();
            } else {
                addLog(`GAGAL: ${res.message || 'Error Server'}`, 'error');
            }
        } catch (err) {
            addLog(`ERROR KONEKSI: ${err.message}`, 'error');
        } finally {
            loadingModal.hide();
        }
    });


    // --- LOGIKA API 3: DIRECT SEND ---
document.getElementById('formDirect').addEventListener('submit', async (e) => {
    e.preventDefault();
    const studyUid = document.getElementById('direct-study').value.trim();

    loadingModal.show();
    addLog(`MEMULAI DIRECT SEND: ${studyUid}`, 'warning');

    try {
        const resp = await fetch('/api/dicom/direct-dcm', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ study: studyUid })
        });
        
        const res = await resp.json();
        
        if (resp.ok) {
            addLog(`BERHASIL: Direct Send Sukses untuk Study UID ${studyUid}`, 'info');
            document.getElementById('formDirect').reset();
        } else {
            addLog(`GAGAL: ${res.message || 'Terjadi kesalahan server'}`, 'error');
        }
    } catch (err) {
        addLog(`KONEKSI ERROR: Gagal menghubungi server backend.`, 'error');
    } finally {
        setTimeout(() => { loadingModal.hide(); }, 800);
    }
});
</script>

</body>
</html>
```

### 13. docker compose

```
dicom-gateway-docker/
├── app/
│   ├── app.py              # Skrip Flask lengkap Anda
│   ├── templates/
│   │   └── dcmpage.html    # File UI Dashboard
│   └── requirements.txt    # Library Python
├── Dockerfile              # Instruksi pembuatan image
└── docker-compose.yml      # Konfigurasi orkestrasi Docker
```
app/requirements.txt
```
flask==3.0.0
flask-restx==1.3.0
requests==2.31.0
werkzeug==3.0.1
```
Dockerfile
```docker
# Gunakan base image Python yang ringan
FROM python:3.10-slim

# Instal dependensi sistem (DCMTK)
RUN apt-get update && apt-get install -y \
    dcmtk \
    && rm -rf /var/lib/apt/lists/*

# Set direktori kerja
WORKDIR /app

# Copy requirements dan instal
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh kode aplikasi
COPY app/ .

# Ekspos port Flask
EXPOSE 5000

# Jalankan aplikasi
CMD ["python", "app.py"]
```
docker-compose.yml
```docker
version: '3.8'

services:
  dicom-gateway:
    build: .
    container_name: dicom-gateway-app
    restart: always
    ports:
      - "5000:5000"
    volumes:
      # Mount folder untuk menyimpan log secara permanen di host
      - ./app_dicom.log:/app/app_dicom.log
    environment:
      - PYTHONUNBUFFERED=1
```

akses swagger-ui dokumentasi
http://192.168.30.14:5000/docs

akses html-ui http://192.168.30.14:5000/

aksea langsung api http://192.168.30.14:5000/api