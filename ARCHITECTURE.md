# DICOM Gateway - Clean Architecture Refactoring

## Project Structure

Aplikasi telah direfactor mengikuti **Clean Architecture** dengan pemisahan concern yang jelas:

```
app/
├── app.py                      # Entry point aplikasi
├── config.py                   # Backward compatibility (legacy)
├── requirements.txt            # Dependencies
├── templates/                  # HTML templates
│   └── dcmpage.html           # Web UI
├── core/                       # Core configuration & utilities
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   └── logger.py              # Logging setup
├── services/                   # Business logic layer
│   ├── __init__.py
│   ├── dicom_service.py       # DICOM processing (modify, send)
│   ├── pacs_service.py        # PACS integration (DCM4CHEE)
│   └── satusehat_service.py   # SatuSehat FHIR API
└── routes/                     # API endpoints layer
    ├── __init__.py
    └── dicom_routes.py        # Flask-RestX routes
```

## Layer Descriptions

### Core Layer (`core/`)
- **config.py**: Centralized configuration management
  - Environment variables loading
  - Application initialization
  - Temp directory setup

- **logger.py**: Logging configuration
  - Rotating file handler setup
  - Consistent logging across application

### Services Layer (`services/`)
Business logic separated into focused services:

- **dicom_service.py**: DICOM file operations
  - `modify_dicom()` - Edit DICOM tags using dcmodify
  - `send_to_router()` - Send files via storescu

- **pacs_service.py**: PACS (DCM4CHEE) integration
  - `get_dicom_metadata()` - Fetch series/SOP UIDs
  - `download_wado()` - Download DICOM files
  - `find_by_accession()` - Search by accession number

- **satusehat_service.py**: SatuSehat FHIR API
  - `fetch_token()` - OAuth2 authentication
  - `fhir_get()` - FHIR resource retrieval
  - `get_imaging_study_id()` - Get ImagingStudy info

### Routes Layer (`routes/`)
- **dicom_routes.py**: API endpoints using Flask-RestX
  - `/api/dicom/process` - Process DICOM with optional modification
  - `/api/dicom/upload` - Upload local DICOM files
  - `/api/dicom/download/<study_uid>` - Download DICOM files
  - `/api/dicom/direct-dcm` - Direct relay by Study UID
  - `/api/dicom/direct-dcm2` - Direct relay by Accession Number
  - `/api/dicom/imageid/<acsn>` - Get ImagingStudy ID from SatuSehat

### Main Application (`app.py`)
- Flask app initialization
- Flask-RestX API setup
- Namespace registration
- Web UI route

## Benefits of Clean Architecture

1. **Separation of Concerns**: Each layer has specific responsibilities
2. **Testability**: Services can be tested independently
3. **Maintainability**: Changes isolated to specific layers
4. **Scalability**: Easy to add new services or endpoints
5. **Reusability**: Services can be used by multiple routes
6. **Readability**: Clear code organization and flow

## Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python app.py

# Access API docs
http://localhost:5000/api/docs
```

## Configuration

Environment variables required in `.env`:
- `DCM4CHEE_URL` - PACS server URL
- `ROUTER_IP` - Router destination IP
- `ROUTER_PORT` - Router destination port
- `ROUTER_AET` - Router AE Title
- `AUTH_URL` - SatuSehat auth endpoint
- `BASE_URL` - SatuSehat FHIR base URL
- `ORG_ID` - Organization ID
- `CLIENT_ID` - OAuth2 client ID
- `CLIENT_SECRET` - OAuth2 client secret
- `LOG_FILE` - Log file path (default: app_dicom.log)
- `TEMP_DIR` - Temporary directory (default: /tmp/dicom_gateway_tmp)
