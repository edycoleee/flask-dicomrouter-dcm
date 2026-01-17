# #app.py
# from flask import Flask, jsonify

# app = Flask(__name__)

# @app.route("/halo", methods=["GET"])
# def halo():
#     return jsonify({"Halo Flask": True})

# if __name__ == "__main__":
#     app.run(host='0.0.0.0',port=5000,debug=True)
#===========================================================

# import subprocess
# from flask import Flask, request, jsonify

# app = Flask(__name__)

# @app.route('/inspect', methods=['GET'])
# def inspect_dicom():
#     # Contoh memanggil 'dcmdump' dari DCMTK
#     file_path = "001.dcm" 
    
#     try:
#         # Menjalankan command OS
#         result = subprocess.run(
#             ['dcmdump', file_path], 
#             capture_output=True, 
#             text=True, 
#             check=True
#         )
#         return jsonify({"status": "success", "output": result.stdout})
#     except subprocess.CalledProcessError as e:
#         return jsonify({"status": "error", "message": e.stderr}), 500

# @app.route("/halo", methods=["GET"])
# def halo():
#     return jsonify({"Halo Flask": True})

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000)

#================================================================

import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

# File contoh yang kita gunakan
FILE_PATH = "001.dcm"

@app.route('/inspect', methods=['GET'])
def inspect_dicom():
    try:
        result = subprocess.run(['dcmdump', FILE_PATH], capture_output=True, text=True, check=True)
        return jsonify({"status": "success", "output": result.stdout})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": e.stderr}), 500

@app.route('/rename', methods=['GET'])
def rename_patient():
    # Mengambil nama baru dari JSON body, contoh: {"new_name": "JOHN^DOE"}
    #data = request.get_json()
    #new_name = data.get("new_name", "ANONYMOUS")
    new_name = "EDY COLE"
    try:
        # dcmodify -i (insert/modify) tag PatientName (0010,0010)
        # -nb (no backup) agar tidak membuat file .bak
        subprocess.run(
            ['dcmodify', '-nb', '-i', f'PatientName={new_name}', FILE_PATH],
            capture_output=True, text=True, check=True
        )
        return jsonify({"status": "success", "message": f"PatientName diubah menjadi {new_name}"})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": e.stderr}), 500

@app.route('/send', methods=['GET'])
def send_dicom():
    # Konfigurasi tujuan (bisa dikirim via JSON atau hardcoded)
    # Contoh: storescu [IP] [PORT] [FILE]
    peer_ip = "192.10.10.28"  # Ganti dengan IP PACS tujuan
    peer_port = "11112"        # Ganti dengan Port PACS tujuan
    ae_title = "DCMROUTER"      # Ganti dengan Called AE Title jika perlu
    
    try:
        # storescu -aec [CalledAET] [IP] [PORT] [FILE]
        # storescu -v -aec DCMROUTER 192.10.10.28 11112 test_direct.dcm
        subprocess.run(
            ['storescu','-aec', ae_title, peer_ip, peer_port, FILE_PATH],
            capture_output=True, text=True, check=True
        )
        return jsonify({"status": "success", "message": f"File berhasil dikirim ke {peer_ip}:{peer_port}"})
    except subprocess.CalledProcessError as e:
        # Jika gagal (misal: PACS tujuan mati), error akan tertangkap di sini
        return jsonify({"status": "error", "message": e.stderr}), 500

@app.route("/halo", methods=["GET"])
def halo():
    return jsonify({"status": "success", "message": "Flask DCMTK siap!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)