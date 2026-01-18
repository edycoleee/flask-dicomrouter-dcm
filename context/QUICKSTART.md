# Quick Start Guide - Clean Architecture Setup

## 📁 Project Structure at a Glance

```
app/
├── app.py                 ← Main entry point (simple!)
├── config.py             ← Legacy wrapper (for backward compatibility)
│
├── core/                 ← Core utilities
│   ├── config.py        ← Configuration management
│   └── logger.py        ← Logging setup
│
├── services/            ← Business Logic (Heart of the app)
│   ├── pacs_service.py       ← PACS/DCM4CHEE operations
│   ├── dicom_service.py      ← DICOM file operations
│   └── satusehat_service.py  ← SatuSehat/FHIR integration
│
├── routes/              ← API Endpoints (Presentation layer)
│   └── dicom_routes.py  ← All API endpoints here
│
├── templates/           ← HTML files
│   └── dcmpage.html
│
└── requirements.txt     ← Dependencies
```

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables
Create a `.env` file in the app directory:
```bash
DCM4CHEE_URL=http://localhost:8080/dcm4chee-arc/aets/DCM4CHEE
ROUTER_IP=192.168.1.100
ROUTER_PORT=104
ROUTER_AET=ROUTER
AUTH_URL=https://auth.satusehat.kemkes.go.id
BASE_URL=https://api.satusehat.kemkes.go.id
ORG_ID=your-org-id
CLIENT_ID=your-client-id
CLIENT_SECRET=your-client-secret
LOG_FILE=app_dicom.log
TEMP_DIR=/tmp/dicom_gateway_tmp
```

### 3. Run the Application
```bash
python app.py
```

The API will be available at `http://localhost:5000`
API documentation at `http://localhost:5000/api/docs`

## 🏗️ Clean Architecture Layers Explained

### Layer 1: Core (`core/`)
**Purpose**: Application setup and configuration
- `config.py` - Loads environment variables, initializes temp folders
- `logger.py` - Sets up logging with rotating file handler

```python
from core.config import Config
from core.logger import setup_logger

Config.init_app()  # Initialize app
logger = setup_logger()  # Setup logging
```

### Layer 2: Services (`services/`)
**Purpose**: Business logic - the real work happens here

#### PACSService
```python
from services.pacs_service import PACSService

# Get DICOM metadata
metadata = PACSService.get_dicom_metadata(study_uid)

# Download DICOM file
PACSService.download_wado(study_uid, metadata, file_path)

# Find by accession number
result, error = PACSService.find_by_accession(accession_num)
```

#### DicomService
```python
from services.dicom_service import DicomService

# Modify DICOM tags
DicomService.modify_dicom(file_path, patient_id="123", acc_num="ACC001")

# Send to router
DicomService.send_to_router(file_path)
```

#### SatusehatService
```python
from services.satusehat_service import SatusehatService

# Get OAuth token
token, error = SatusehatService.fetch_token()

# Make FHIR API calls
data, status = SatusehatService.fhir_get(url, token)

# Get ImagingStudy info
result, error = SatusehatService.get_imaging_study_id(accession)
```

### Layer 3: Routes (`routes/`)
**Purpose**: API endpoints - connects services to HTTP

```python
from routes.dicom_routes import dicom_ns

# Routes available:
# POST   /api/dicom/process       - Process DICOM with optional mods
# POST   /api/dicom/upload        - Upload and process local file
# GET    /api/dicom/download/<id> - Download DICOM file
# POST   /api/dicom/direct-dcm    - Direct relay by Study UID
# POST   /api/dicom/direct-dcm2   - Direct relay by Accession #
# GET    /api/dicom/imageid/<acsn> - Get ImagingStudy ID
```

## 💡 How the Flow Works

### Example: Process DICOM Workflow

```
1. HTTP POST /api/dicom/process
   ↓
2. Route Handler (routes/dicom_routes.py)
   ↓
3. PACSService.get_dicom_metadata() ← Gets metadata from PACS
   ↓
4. PACSService.download_wado() ← Downloads the file
   ↓
5. DicomService.modify_dicom() ← Modifies tags (optional)
   ↓
6. DicomService.send_to_router() ← Sends to router
   ↓
7. HTTP 200 Response
```

## 🔍 Code Examples

### Adding a New Service

```python
# services/my_new_service.py
from core.logger import setup_logger

logger = setup_logger()

class MyNewService:
    @staticmethod
    def do_something(param):
        """Do something amazing"""
        logger.info(f"Doing something with {param}")
        # Your logic here
        return result
```

### Using Service in a Route

```python
# In routes/dicom_routes.py
from services.my_new_service import MyNewService

@dicom_ns.route('/my-endpoint')
class MyEndpoint(Resource):
    def post(self):
        data = dicom_ns.payload
        result = MyNewService.do_something(data['param'])
        return {"status": "success", "data": result}, 200
```

### Adding a New API Endpoint

```python
# In routes/dicom_routes.py
from services.pacs_service import PACSService

@dicom_ns.route('/new-operation')
class NewOperation(Resource):
    def post(self):
        """New operation description"""
        data = dicom_ns.payload
        
        try:
            # Use services
            result = PACSService.find_by_accession(data['accession'])
            return {"status": "success", "data": result}, 200
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}")
            return {"status": "error", "message": str(e)}, 500
```

## 📚 Architecture Benefits

| Aspect | Before | After |
|--------|--------|-------|
| **Monolith** | 351-line app.py | 32-line app.py |
| **Testing** | Hard to test | Easy (test services) |
| **Reuse** | Code duplication | Services reusable |
| **Changes** | Affects whole app | Isolated to layer |
| **New features** | Modify app.py | Add service + route |
| **Readability** | Confusing | Clear separation |

## 🐛 Troubleshooting

### Import Errors
Ensure you're running from the app directory and Python path includes app root:
```bash
cd /home/sultan/flask/flask-dicomrouter-dcm/app
python app.py
```

### Module Not Found
Check that folders have `__init__.py`:
```bash
# core, services, routes folders should have __init__.py
ls core/__init__.py services/__init__.py routes/__init__.py
```

### Configuration Issues
Verify `.env` file exists and has all required variables:
```bash
cat .env  # Check environment variables
```

## 📖 More Information

- See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed architecture documentation
- See [REFACTORING_SUMMARY.md](./REFACTORING_SUMMARY.md) for refactoring details
- See [README.md](./README.md) for project overview

## 🎯 Next Steps

1. ✅ Understand the layer structure
2. ✅ Explore services in `services/` folder
3. ✅ Check API endpoints in `routes/dicom_routes.py`
4. ✅ Test endpoints using `/api/docs`
5. ✅ Extend with new services/endpoints as needed
