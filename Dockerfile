# # Gunakan base image Python yang ringan
# FROM python:3.10-slim

# # Instal dependensi sistem (DCMTK)
# RUN apt-get update && apt-get install -y \
#     dcmtk \
#     && rm -rf /var/lib/apt/lists/*

# # Set direktori kerja
# WORKDIR /app

# # Copy requirements dan instal
# COPY app/requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy seluruh kode aplikasi
# COPY app/ .

# # Ekspos port Flask
# EXPOSE 5000

# # Jalankan aplikasi
# CMD ["python", "app.py"]

# ================================

# FROM python:3.10-slim

# # Instal DCMTK dan utility pendukung
# RUN apt-get update && apt-get install -y \
#     dcmtk \
#     procps \
#     && rm -rf /var/lib/apt/lists/*

# WORKDIR /app

# # Instal dependensi Python
# COPY app/requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy source code
# COPY app/ .

# # Buat folder log dan folder temporary
# # Folder /temporary ini yang akan digunakan oleh aplikasi
# RUN touch app_dicom.log && chmod 666 app_dicom.log \
#     && mkdir -p /temporary && chmod 777 /temporary
    
# EXPOSE 5000

# CMD ["python", "app.py"]
#=====================================================
FROM python:3.10-slim

# 1. Instal DCMTK (storescu, dcmodify)
RUN apt-get update && apt-get install -y \
    dcmtk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Instal dependensi
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# 3. Copy source code
COPY app/ .

# 4. Setup Folder & Izin (Gunakan /tmp/dicom_gateway_tmp sesuai config Python)
RUN mkdir -p /tmp/dicom_gateway_tmp && chmod 777 /tmp/dicom_gateway_tmp \
    && touch app_dicom.log && chmod 666 app_dicom.log

EXPOSE 5000

# 5. Jalankan Gunicorn
# --workers 4: Menangani 4 request paralel
# --timeout 120: Mengakomodasi download file DICOM yang besar
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]