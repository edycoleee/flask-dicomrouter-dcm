# DICOM Gateway API Specifications

Dokumentasi lengkap semua API endpoints yang tersedia di DICOM Router Gateway.

---

## Base URL

```
http://localhost:5000/api
```

## Namespaces

- **`/dicom`** - DICOM Router & PACS Processing
- **`/satset`** - SatuSehat FHIR Integration Endpoints

---

# DICOM Namespace (`/api/dicom`)

## 1. Process DICOM (Unified)

**Endpoint:** `POST /dicom/process`

**Description:** 
Unified DICOM processing endpoint yang mendukung:
- Proses berdasarkan Study UID
- Proses berdasarkan Accession Number
- Modifikasi metadata (Patient ID dan/atau Accession Number)
- Mengirim SEMUA instance dari study ke router

**Request Body:**
```json
{
  "study": "1.3.46.67...",
  "patientid": "PID-12345",
  "accesionnum": "ACC-XXXX"
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| study | string | No | Study UID (Optional, gunakan Accession Number jika tidak ada) |
| patientid | string | No | Patient ID untuk modifikasi |
| accesionnum | string | No | Accession Number untuk lookup atau modifikasi |

**Response (200 OK):**
```json
{
  "status": "success",
  "study_uid": "1.3.46.67...",
  "total_instance": 5,
  "sent_instance": 5,
  "failed_instance": 0,
  "patient_modified": true,
  "accession_modified": false,
  "router": "192.10.10.28:11112"
}
```

**Response (207 Multi-Status - Partial Success):**
```json
{
  "status": "partial_error",
  "study_uid": "1.3.46.67...",
  "total_instance": 5,
  "sent_instance": 3,
  "failed_instance": 2,
  "failed_details": [
    {"instance": 0, "error": "Connection timeout"},
    {"instance": 2, "error": "Invalid DICOM format"}
  ],
  "router": "192.10.10.28:11112"
}
```

---

## 2. Upload DICOM File

**Endpoint:** `POST /dicom/upload`

**Description:** 
Upload file DICOM lokal, modifikasi metadata, lalu kirim ke Router.

**Request Type:** `multipart/form-data`

**Form Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | file | Yes | DICOM file (.dcm) |
| patientid | string | No | Patient ID untuk modifikasi |
| accesionnum | string | No | Accession Number untuk modifikasi |

**Response (200 OK):**
```json
{
  "status": "success",
  "file": "sample.dcm",
  "message": "File sample.dcm berhasil diunggah dan dikirim ke Router"
}
```

**Response (400 Bad Request):**
```json
{
  "status": "error",
  "message": "No file selected"
}
```

---

## 3. Upload DICOM to PACS (STOW-RS)

**Endpoint:** `POST /dicom/pacs/upload`

**Description:**
Upload file DICOM lokal ke DCM4CHEE (PACS) via STOW-RS.

**Request Type:** `multipart/form-data`

**Form Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | file | Yes | DICOM file (.dcm) |

**Response (200 OK):**
```json
{
  "status": "success",
  "pacs_status": 200,
  "file": "sample.dcm",
  "response": {}
}
```

**Response (4xx/5xx):**
```json
{
  "status": "error",
  "pacs_status": 403,
  "response": {
    "errorMessage": "..."
  }
}
```

---

## 4. Delete Study from PACS

**Endpoint:** `DELETE /dicom/pacs/studies/<study_uid>`

**Description:**
Hapus study di DCM4CHEE (PACS) berdasarkan Study UID.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| study_uid | string | Study Instance UID |

**Response (200 OK):**
```json
{
  "status": "success",
  "pacs_status": 200,
  "study_uid": "1.2.840....",
  "response": {}
}
```

**Response (4xx/5xx):**
```json
{
  "status": "error",
  "pacs_status": 403,
  "response": {
    "errorMessage": "..."
  }
}
```

---

## 5. Get DICOM Info from Local File

**Endpoint:** `POST /dicom/get-info`

**Description:**
Baca Study UID, Accession Number, dan Patient ID dari file DICOM lokal.

**Request Type:** `multipart/form-data`

**Form Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | file | Yes | DICOM file (.dcm) |

**Response (200 OK):**
```json
{
  "status": "success",
  "study_uid": "1.2.840....",
  "accession_number": "202512300002",
  "patient_id": "P00001349322"
}
```

---

## 6. Download DICOM File

**Endpoint:** `GET /dicom/download/<study_uid>`

**Description:** 
Download DICOM file dari PACS berdasarkan Study UID.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| study_uid | string | Study Instance UID |

**Response (200 OK):**
- Binary DICOM file dengan header: `Content-Disposition: attachment; filename="<study_uid>.dcm"`

**Response (500 Error):**
```json
{
  "error": "Study not found in PACS"
}
```

---

# SatuSehat Namespace (`/api/satset`)

## 1. Create Encounter

**Endpoint:** `POST /satset/encounter`

**Description:** 
Buat Encounter resource di SatuSehat FHIR Server.

**Request Body:**
```json
{
  "identifier_value": "RG2023I0000175",
  "subject_id": "P10443013727",
  "subject_display": "MILA YASYFI TASBIHA",
  "practitioner_id": "10016869420",
  "practitioner_display": "dr. ARIAWAN SETIADI, Sp.A",
  "period_start": "2025-08-01T05:57:41+00:00",
  "period_end": "2025-08-01T06:07:41+00:00",
  "location_id": "ecff1c64-3f62-4469-b577-ea38f263b276",
  "location_display": "Ruang 1, Poliklinik Anak, Lantai 1, Gedung Poliklinik"
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| identifier_value | string | Yes | No register / identifier value |
| subject_id | string | Yes | Patient ID (akan di-prefix dengan 'Patient/') |
| subject_display | string | Yes | Patient display name |
| practitioner_id | string | Yes | Practitioner ID (akan di-prefix dengan 'Practitioner/') |
| practitioner_display | string | Yes | Practitioner display name |
| period_start | string | Yes | Period start (ISO8601 format) |
| period_end | string | No | Period end (ISO8601 format, optional) |
| location_id | string | Yes | Location ID (akan di-prefix dengan 'Location/') |
| location_display | string | Yes | Location display name |

**Response (201 Created):**
```json
{
  "status": "success",
  "encounter_id": "015aa41f-88d7-4b0b-b5f1-d511522bfa87",
  "resource": {
    "resourceType": "Encounter",
    "id": "015aa41f-88d7-4b0b-b5f1-d511522bfa87",
    ...
  }
}
```

**Response (400 Bad Request):**
```json
{
  "status": "error",
  "message": "Missing required field: subject_id"
}
```

---

## 2. Create Service Request

**Endpoint:** `POST /satset/service-req`

**Description:** 
Buat ServiceRequest resource di SatuSehat FHIR Server.

**Request Body:**
```json
{
  "identifier_value": "RG2023I0000176",
  "noacsn": "20250002",
  "subject_id": "P10443013727",
  "encounter_id": "015aa41f-88d7-4b0b-b5f1-d511522bfa87",
  "period_start": "2025-08-31T15:25:00+00:00",
  "practitioner_id": "10016869420",
  "practitioner_display": "dr. ARIAWAN SETIADI, Sp.A",
  "performer_id": "10000504193",
  "performer_display": "dr. RINI SUSANTI, Sp.Rad"
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| identifier_value | string | Yes | No register / identifier value |
| noacsn | string | Yes | Accession Number (NOACSN) |
| subject_id | string | Yes | Patient ID (akan di-prefix dengan 'Patient/') |
| encounter_id | string | Yes | Encounter ID (akan di-prefix dengan 'Encounter/') |
| period_start | string | Yes | Occurrence datetime (ISO8601) |
| practitioner_id | string | Yes | Requester ID (akan di-prefix dengan 'Practitioner/') |
| practitioner_display | string | Yes | Requester display name |
| performer_id | string | Yes | Performer ID (akan di-prefix dengan 'Practitioner/') |
| performer_display | string | Yes | Performer display name |

**Response (201 Created):**
```json
{
  "status": "success",
  "service_request_id": "a33163ec-ba77-4775-8d20-83035b76e668",
  "resource": {
    "resourceType": "ServiceRequest",
    "id": "a33163ec-ba77-4775-8d20-83035b76e668",
    ...
  }
}
```

---

## 3. Create Observation

**Endpoint:** `POST /satset/observation`

**Description:** 
Buat Observation resource di SatuSehat FHIR Server.

**Request Body:**
```json
{
  "identifier_value": "RG2023I0000174",
  "codind_code": "24648-8",
  "coding_display": "XR Chest PA upright",
  "subject_id": "P10443013727",
  "subject_display": "MILA YASYFI TASBIHA",
  "encounter_id": "6dc2dc13-0b5a-4105-996e-6403e43be60a",
  "period_start": "2025-08-31T15:25:00+00:00",
  "performer_id": "10000504193",
  "performer_display": "dr. RINI SUSANTI, Sp.Rad",
  "performer_value": "Hasil Bacaan adalah ...",
  "service_request_id": "a33163ec-ba77-4775-8d20-83035b76e668",
  "imaging_study_id": "75b7e9d0-c079-419c-84f8-8dba7b9cd585"
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| identifier_value | string | Yes | No register / identifier value |
| codind_code | string | Yes | Coding code (LOINC) |
| coding_display | string | Yes | Coding display text |
| subject_id | string | Yes | Patient ID (akan di-prefix dengan 'Patient/') |
| subject_display | string | Yes | Patient display name |
| encounter_id | string | Yes | Encounter ID (akan di-prefix dengan 'Encounter/') |
| period_start | string | Yes | Effective datetime (ISO8601) |
| performer_id | string | Yes | Performer ID (akan di-prefix dengan 'Practitioner/') |
| performer_display | string | Yes | Performer display name |
| performer_value | string | Yes | Result/Finding text |
| service_request_id | string | No | ServiceRequest ID reference (optional) |
| imaging_study_id | string | No | ImagingStudy ID reference (optional) |

**Response (201 Created):**
```json
{
  "status": "success",
  "observation_id": "82b9af58-c98d-4263-9a6f-9a04fdfec43a",
  "resource": {
    "resourceType": "Observation",
    "id": "82b9af58-c98d-4263-9a6f-9a04fdfec43a",
    ...
  }
}
```

---

## 4. Create Diagnostic Report

**Endpoint:** `POST /satset/diag-rep`

**Description:** 
Buat DiagnosticReport resource di SatuSehat FHIR Server.

**Request Body:**
```json
{
  "identifier_value": "RG2023I0000174",
  "codind_code": "24648-8",
  "coding_display": "XR Chest PA upright",
  "subject_id": "P10443013727",
  "encounter_id": "6dc2dc13-0b5a-4105-996e-6403e43be60a",
  "period_start": "2025-08-31T15:25:00+00:00",
  "performer_id": "10000504193",
  "imaging_study_id": "75b7e9d0-c079-419c-84f8-8dba7b9cd585",
  "observation_id": "82b9af58-c98d-4263-9a6f-9a04fdfec43a",
  "service_request_id": "a33163ec-ba77-4775-8d20-83035b76e668",
  "conclusion_text": "Hasil Bacaan adalah Tak tampak bercak pada kedua lapangan paru"
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| identifier_value | string | Yes | No register / identifier value |
| codind_code | string | Yes | Coding code (LOINC) |
| coding_display | string | Yes | Coding display text |
| subject_id | string | Yes | Patient ID (akan di-prefix dengan 'Patient/') |
| encounter_id | string | Yes | Encounter ID (akan di-prefix dengan 'Encounter/') |
| period_start | string | Yes | Effective datetime (ISO8601) |
| performer_id | string | Yes | Performer ID (akan di-prefix dengan 'Practitioner/') |
| imaging_study_id | string | No | ImagingStudy ID reference (optional) |
| observation_id | string | No | Observation ID reference (optional) |
| service_request_id | string | No | ServiceRequest ID reference (optional) |
| conclusion_text | string | No | Conclusion/Finding text (optional) |

**Response (201 Created):**
```json
{
  "status": "success",
  "diagnostic_report_id": "d48f8b92-c1a1-4c8a-9e7f-6b4c8d9a1f2e",
  "resource": {
    "resourceType": "DiagnosticReport",
    "id": "d48f8b92-c1a1-4c8a-9e7f-6b4c8d9a1f2e",
    ...
  }
}
```

---

## 5. Get ImagingStudy ID by Accession Number

**Endpoint:** `GET /satset/imageid/<accession_number>`

**Description:** 
Cari ImagingStudy ID dari SatuSehat berdasarkan Accession Number.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| acsn | string | Accession Number dari PACS/SatuSehat |

**Response (200 OK):**
```json
{
  "status": "success",
  "imagingStudy_id": "75b7e9d0-c079-419c-84f8-8dba7b9cd585",
  "patient_reference": "Patient/P10443013727"
}
```

**Response (404 Not Found):**
```json
{
  "status": "error",
  "message": "Accession number not found in SatuSehat"
}
```

---

# Response Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource successfully created |
| 207 | Multi-Status - Partial success (some instances failed) |
| 400 | Bad Request - Invalid input parameters |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error |
| 502 | Bad Gateway - Authentication failed or external service error |

---

# Error Response Format

Semua endpoint error akan mengembalikan format:

```json
{
  "status": "error",
  "message": "Deskripsi error yang terjadi"
}
```

Atau untuk validasi:

```json
{
  "status": "error",
  "message": "Missing required field: field_name"
}
```

---

# DateTime Format

Semua datetime field harus menggunakan **ISO8601 format**:

```
2025-08-31T15:25:00+00:00
atau
2025-08-31T15:25:00Z
```

---

# Example Workflow

## Workflow Lengkap: Dari DICOM ke FHIR

### 1. Buat Encounter
```bash
POST /api/satset/encounter
{
  "identifier_value": "RG2023I0000175",
  "subject_id": "P10443013727",
  "subject_display": "MILA YASYFI TASBIHA",
  "practitioner_id": "10016869420",
  "practitioner_display": "dr. ARIAWAN SETIADI, Sp.A",
  "period_start": "2025-08-31T15:25:00+00:00",
  "location_id": "ecff1c64-3f62-4469-b577-ea38f263b276",
  "location_display": "Ruang 1, Poliklinik Anak"
}
```
Response: `encounter_id = "015aa41f-88d7-4b0b-b5f1-d511522bfa87"`

### 2. Buat Service Request
```bash
POST /api/satset/service-req
{
  "identifier_value": "RG2023I0000176",
  "noacsn": "20250002",
  "subject_id": "P10443013727",
  "encounter_id": "015aa41f-88d7-4b0b-b5f1-d511522bfa87",
  "period_start": "2025-08-31T15:25:00+00:00",
  "practitioner_id": "10016869420",
  "practitioner_display": "dr. ARIAWAN SETIADI, Sp.A",
  "performer_id": "10000504193",
  "performer_display": "dr. RINI SUSANTI, Sp.Rad"
}
```
Response: `service_request_id = "a33163ec-ba77-4775-8d20-83035b76e668"`

### 3. Process DICOM (dari PACS)
```bash
POST /api/dicom/process
{
  "accesionnum": "20250002"
}
```
DICOM akan diunduh dari PACS dan dikirim ke Router

### 4. Cari ImagingStudy ID
```bash
GET /api/satset/imageid/20250002
```
Response: `imaging_study_id = "75b7e9d0-c079-419c-84f8-8dba7b9cd585"`

### 5. Buat Observation
```bash
POST /api/satset/observation
{
  "identifier_value": "RG2023I0000174",
  "codind_code": "24648-8",
  "coding_display": "XR Chest PA upright",
  "subject_id": "P10443013727",
  "subject_display": "MILA YASYFI TASBIHA",
  "encounter_id": "015aa41f-88d7-4b0b-b5f1-d511522bfa87",
  "period_start": "2025-08-31T15:25:00+00:00",
  "performer_id": "10000504193",
  "performer_display": "dr. RINI SUSANTI, Sp.Rad",
  "performer_value": "Tidak ada kelainan",
  "service_request_id": "a33163ec-ba77-4775-8d20-83035b76e668",
  "imaging_study_id": "75b7e9d0-c079-419c-84f8-8dba7b9cd585"
}
```
Response: `observation_id = "82b9af58-c98d-4263-9a6f-9a04fdfec43a"`

### 6. Buat Diagnostic Report
```bash
POST /api/satset/diag-rep
{
  "identifier_value": "RG2023I0000174",
  "codind_code": "24648-8",
  "coding_display": "XR Chest PA upright",
  "subject_id": "P10443013727",
  "encounter_id": "015aa41f-88d7-4b0b-b5f1-d511522bfa87",
  "period_start": "2025-08-31T15:25:00+00:00",
  "performer_id": "10000504193",
  "imaging_study_id": "75b7e9d0-c079-419c-84f8-8dba7b9cd585",
  "observation_id": "82b9af58-c98d-4263-9a6f-9a04fdfec43a",
  "service_request_id": "a33163ec-ba77-4775-8d20-83035b76e668",
  "conclusion_text": "Tidak ada kelainan pada kedua lapangan paru"
}
```
Response: `diagnostic_report_id = "d48f8b92-c1a1-4c8a-9e7f-6b4c8d9a1f2e"`

---

# API Documentation UI

Swagger UI tersedia di: `http://localhost:5000/api/docs`

---

# Notes

- Semua ID yang tidak memiliki prefix (seperti Patient ID) akan otomatis di-prefix sesuai dengan tipe resource-nya
- Format datetime HARUS ISO8601, contoh: `2025-08-31T15:25:00+00:00`
- Optional fields boleh dikosongkan (tidak perlu disertakan dalam request body)
- Setiap request ke FHIR Server akan melakukan autentikasi terlebih dahulu
- Rate limiting dan authentication dapat dikonfigurasi di `core/config.py`
