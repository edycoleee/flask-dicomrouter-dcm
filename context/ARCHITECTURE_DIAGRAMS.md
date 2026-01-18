# Clean Architecture Diagram & Data Flow

## 🏗️ Overall Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                       │
│                                                                   │
│                    Flask-RestX Routes (HTTP)                    │
│                  /api/dicom/* endpoints                         │
│                                                                   │
│  ┌────────────────┬──────────────┬──────────────┬──────────────┐ │
│  │   /process     │   /upload    │  /download   │  /direct-dcm │ │
│  │   /direct-dcm2 │  /imageid    │              │              │ │
│  └────────────────┴──────────────┴──────────────┴──────────────┘ │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BUSINESS LOGIC LAYER                        │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Services (Independent, Reusable, Testable)            │  │
│  │                                                          │  │
│  │  ┌──────────────────┐  ┌──────────────────┐            │  │
│  │  │  PACSService     │  │  DicomService    │            │  │
│  │  ├──────────────────┤  ├──────────────────┤            │  │
│  │  │ • get_metadata   │  │ • modify_dicom   │            │  │
│  │  │ • download_wado  │  │ • send_to_router │            │  │
│  │  │ • find_by_acc    │  └──────────────────┘            │  │
│  │  └──────────────────┘                                   │  │
│  │                                                          │  │
│  │  ┌──────────────────────────────────────┐              │  │
│  │  │  SatusehatService                    │              │  │
│  │  ├──────────────────────────────────────┤              │  │
│  │  │ • fetch_token                        │              │  │
│  │  │ • fhir_get                           │              │  │
│  │  │ • get_imaging_study_id               │              │  │
│  │  └──────────────────────────────────────┘              │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                        │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Core Utilities                                          │  │
│  │  ┌──────────────────┐         ┌──────────────────────┐  │  │
│  │  │  Configuration   │         │  Logging             │  │  │
│  │  │  • Load .env     │         │  • Setup handlers    │  │  │
│  │  │  • Initialize    │         │  • Format messages   │  │  │
│  │  │  • Temp folders  │         │  • Rotate logs       │  │  │
│  │  └──────────────────┘         └──────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SYSTEMS                            │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   DCM4CHEE   │  │   Storage    │  │  SatuSehat   │           │
│  │   (PACS)     │  │   Router     │  │   FHIR API   │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow Examples

### Example 1: Process DICOM with Modification

```
                         HTTP Request
                              │
                 POST /api/dicom/process
                 { "study": "1.2.3", 
                   "patientid": "P123" }
                              │
                              ▼
                    ┌──────────────────┐
                    │  Routes Layer    │
                    │ ProcessDicom     │
                    └────────┬─────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
      ┌──────────────┐ ┌──────────────┐ ┌─────────────┐
      │ PACSService  │ │ PACSService  │ │DicomService │
      │   .get_      │ │  .download   │ │  .modify    │
      │  metadata()  │ │   _wado()    │ │  _dicom()   │
      └────────┬─────┘ └──────┬───────┘ └────────┬────┘
               │              │                   │
               ▼              ▼                   ▼
          DCM4CHEE      DCM4CHEE         dcmodify
         Metadata       Download File    Command
          Response
               │              │                   │
               └────────────────┬──────────────────┘
                                │
                    ┌───────────▼────────────┐
                    │  DicomService         │
                    │  .send_to_router()    │
                    └───────────┬────────────┘
                                │
                                ▼
                          Router (DICOM)
                          Send via C-STORE
                                │
                                ▼
                         ┌───────────────┐
                    HTTP │  Return JSON  │
                    200  │  "success"    │
                         └───────────────┘
```

### Example 2: Find by Accession Number

```
            HTTP Request
                 │
    POST /api/dicom/direct-dcm2
    { "accesionnum": "ACC123" }
                 │
                 ▼
          ┌─────────────────┐
          │ DirectDicom2    │
          │ Routes Handler  │
          └────────┬────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │ PACSService         │
         │ .find_by_accession()│
         └────────┬────────────┘
                  │
     ┌────────────┴─────────────┐
     │                          │
     ▼                          ▼
Query PACS          Get Metadata
for Accession       by Study UID
                    │
     ┌──────────────┴──────────┐
     │                         │
     ▼                         ▼
Get Study UID       Series & SOP UIDs
     │                        │
     └────────────┬───────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ PACSService     │
         │ .download_wado()│
         └────────┬────────┘
                  │
                  ▼
            Download File
                  │
                  ▼
         ┌─────────────────────┐
         │ DicomService        │
         │ .send_to_router()   │
         └────────┬────────────┘
                  │
                  ▼
            Send to Router
                  │
                  ▼
         HTTP 200 with Details
```

### Example 3: Get ImagingStudy ID from SatuSehat

```
            HTTP Request
                 │
    GET /api/dicom/imageid/ACC123
                 │
                 ▼
          ┌──────────────────┐
          │ ImageId Route    │
          └────────┬─────────┘
                   │
                   ▼
      ┌──────────────────────────┐
      │ SatusehatService         │
      │ .get_imaging_study_id()  │
      └────────┬─────────────────┘
               │
               ├──────────────────────┐
               │                      │
               ▼                      ▼
        .fetch_token()          FHIR API Search
               │                      │
               ▼                      ▼
          Auth Server          Bundle Response
               │                      │
               ├──────────┬───────────┘
               │          │
               ▼          ▼
        Access Token   Find ImagingStudy
               │
               └──────────┬──────────┘
                          │
                          ▼
                   ┌─────────────────┐
                   │ Extract ID & Ref│
                   └────────┬────────┘
                            │
                            ▼
                    HTTP 200 Response
                    {
                      "status": "success",
                      "imagingStudy_id": "IS123",
                      "patient_reference": "Patient/P456"
                    }
```

## 📊 Dependency Graph

```
Routes Layer
    ├── ProcessDicom
    │   ├── PACSService (get_metadata, download_wado)
    │   ├── DicomService (modify_dicom, send_to_router)
    │   └── Config (TEMP_DIR)
    │
    ├── UploadDicom
    │   ├── DicomService (modify_dicom, send_to_router)
    │   └── Config (TEMP_DIR)
    │
    ├── DownloadDicom
    │   ├── PACSService (get_metadata, download_wado)
    │   └── Config (TEMP_DIR)
    │
    ├── DirectDicom
    │   ├── PACSService (get_metadata, download_wado)
    │   ├── DicomService (send_to_router)
    │   └── Config (TEMP_DIR)
    │
    ├── DirectDicom2
    │   ├── PACSService (find_by_accession, download_wado)
    │   ├── DicomService (send_to_router)
    │   └── Config (TEMP_DIR)
    │
    └── ImageId
        ├── SatusehatService (get_imaging_study_id)
        └── Logger

Services (No cross-dependencies, all independent)
    ├── PACSService
    │   └── Config (DCM4CHEE_URL, TEMP_DIR)
    │
    ├── DicomService
    │   └── Config (ROUTER_IP, ROUTER_PORT, ROUTER_AET)
    │
    └── SatusehatService
        └── Config (AUTH_URL, BASE_URL, ORG_ID, etc)

Core (Shared utilities)
    ├── Config
    └── Logger
```

## 🎯 Request-Response Cycle

```
Client
   │
   │ HTTP Request
   ▼
Flask App (app.py)
   │ • Routes request to namespace
   │ • Passes to Resource class
   ▼
Routes/Resource Handler (dicom_routes.py)
   │ • Extract parameters
   │ • Validate input
   │ • Delegate to services
   ▼
Service Layer (services/*.py)
   │ • Execute business logic
   │ • Make external API calls
   │ • Log operations
   ▼
External Systems
   │ • DCM4CHEE/PACS
   │ • Router/DICOM
   │ • SatuSehat/FHIR
   │
   │ ◄─── Response
   │
   ▼
Service (return result)
   │
   ▼
Route Handler (format response)
   │
   ▼
Flask (HTTP Response)
   │
   ▼
Client ← HTTP 200 + JSON
```

## 🔌 Integration Points

```
┌─────────────────────────────────────────────────────┐
│            DICOM Gateway Application                │
├──────┬──────────────────────────────────────┬───────┤
│      │  Services (Business Logic)           │       │
│      │                                      │       │
│ HTTP │  • PACSService                       │ .env  │
│ ▲    │  • DicomService                      │ ▲     │
│ │    │  • SatusehatService                  │ │     │
│ │    │                                      │ │     │
└─┼────┴──────────────────────────────────────┴─┼─────┘
  │                                              │
  │                                              │
  ├──────────────────┬──────────────────┬───────┘
  │                  │                  │
  ▼                  ▼                  ▼
DCM4CHEE          Router            SatuSehat
(PACS)            (DICOM)           (FHIR API)
  │                  │                  │
  ├─ GET /rs/        ├─ storescu        ├─ OAuth2
  └─ WADO protocol   │  C-STORE         └─ GET /resources
```

## 💾 Data Flow in Code

```python
# Example: Process workflow
@dicom_ns.route('/process')
class ProcessDicom(Resource):
    def post(self):
        # 1. Input Validation
        data = dicom_ns.payload  # {"study": "...", ...}
        study_uid = data['study']
        
        # 2. Service Calls (layered)
        meta = PACSService.get_dicom_metadata(study_uid)
        # ↓ makes HTTP request to DCM4CHEE
        # ↓ returns {"series": "...", "sop": "..."}
        
        PACSService.download_wado(study_uid, meta, local_path)
        # ↓ downloads file to disk
        
        DicomService.modify_dicom(local_path, p_id, acc)
        # ↓ runs dcmodify command
        
        DicomService.send_to_router(local_path)
        # ↓ runs storescu command
        
        # 3. Response
        return {"status": "success"}, 200
```
