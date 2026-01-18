# Testing Guide - Clean Architecture

## 🧪 Testing Strategy for Clean Architecture

With clean architecture, testing becomes much easier since services are independent and testable.

## Unit Tests for Services

### Testing PACSService

```python
# tests/test_pacs_service.py
import pytest
from unittest.mock import patch, MagicMock
from services.pacs_service import PACSService

class TestPACSService:
    
    @patch('services.pacs_service.requests.get')
    def test_get_dicom_metadata(self, mock_get):
        """Test getting DICOM metadata from PACS"""
        # Arrange
        study_uid = "1.2.3.4.5"
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "0020000E": {"Value": ["1.2.3.4.5.1"]},  # Series UID
                "00080018": {"Value": ["1.2.3.4.5.1.1"]}  # SOP UID
            }
        ]
        mock_get.return_value = mock_response
        
        # Act
        result = PACSService.get_dicom_metadata(study_uid)
        
        # Assert
        assert result["series"] == "1.2.3.4.5.1"
        assert result["sop"] == "1.2.3.4.5.1.1"
        mock_get.assert_called_once()
    
    @patch('services.pacs_service.requests.get')
    def test_find_by_accession_success(self, mock_get):
        """Test finding DICOM by accession number"""
        # Arrange
        accession = "ACC123"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "not empty"
        mock_response.json.side_effect = [
            [{"0020000D": {"Value": ["1.2.3.4.5"]}}],  # First call - studies
            [{"0020000E": {"Value": ["1.2.3.4.5.1"]}, 
              "00080018": {"Value": ["1.2.3.4.5.1.1"]}}]  # Second call - metadata
        ]
        mock_get.return_value = mock_response
        
        # Act
        result, error = PACSService.find_by_accession(accession)
        
        # Assert
        assert error is None
        assert result["study"] == "1.2.3.4.5"
        assert result["series"] == "1.2.3.4.5.1"
        assert result["sop"] == "1.2.3.4.5.1.1"
    
    @patch('services.pacs_service.requests.get')
    def test_find_by_accession_not_found(self, mock_get):
        """Test finding DICOM by accession when not found"""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = ""
        mock_get.return_value = mock_response
        
        # Act
        result, error = PACSService.find_by_accession("NOTFOUND")
        
        # Assert
        assert result is None
        assert error is not None
        assert "tidak ditemukan" in error
    
    @patch('services.pacs_service.requests.get')
    def test_download_wado(self, mock_get):
        """Test downloading DICOM file via WADO"""
        # Arrange
        study_uid = "1.2.3.4.5"
        meta = {"series": "1.2.3.4.5.1", "sop": "1.2.3.4.5.1.1"}
        temp_file = "/tmp/test.dcm"
        
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"dicom_data"]
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_get.return_value = mock_response
        
        # Act
        with patch("builtins.open", create=True):
            PACSService.download_wado(study_uid, meta, temp_file)
        
        # Assert
        mock_get.assert_called_once()
```

### Testing DicomService

```python
# tests/test_dicom_service.py
import pytest
from unittest.mock import patch, MagicMock, call
from services.dicom_service import DicomService

class TestDicomService:
    
    @patch('services.dicom_service.subprocess.run')
    @patch('services.dicom_service.os.path.exists')
    @patch('services.dicom_service.os.remove')
    def test_modify_dicom(self, mock_remove, mock_exists, mock_run):
        """Test DICOM tag modification"""
        # Arrange
        file_path = "/tmp/test.dcm"
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        mock_exists.return_value = True
        
        # Act
        DicomService.modify_dicom(file_path, patient_id="P123", acc_num="ACC001")
        
        # Assert
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "dcmodify" in call_args
        assert "(0010,0020)=P123" in call_args
        assert "(0008,0050)=ACC001" in call_args
        mock_remove.assert_called_once()  # Remove .bak file
    
    @patch('services.dicom_service.subprocess.run')
    def test_modify_dicom_failure(self, mock_run):
        """Test DICOM modification failure"""
        # Arrange
        file_path = "/tmp/test.dcm"
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error message"
        mock_run.return_value = mock_result
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            DicomService.modify_dicom(file_path)
        assert "dcmodify error" in str(exc_info.value)
    
    @patch('services.dicom_service.subprocess.run')
    def test_send_to_router_success(self, mock_run):
        """Test sending DICOM to router"""
        # Arrange
        file_path = "/tmp/test.dcm"
        mock_result = MagicMock()
        mock_result.stdout = "Received Store Response (Success)"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Act
        DicomService.send_to_router(file_path)
        
        # Assert
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "storescu" in call_args
    
    @patch('services.dicom_service.subprocess.run')
    def test_send_to_router_failure(self, mock_run):
        """Test sending DICOM to router fails"""
        # Arrange
        file_path = "/tmp/test.dcm"
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "Connection refused"
        mock_run.return_value = mock_result
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            DicomService.send_to_router(file_path)
        assert "StoreSCU Failed" in str(exc_info.value)
```

### Testing SatusehatService

```python
# tests/test_satusehat_service.py
import pytest
from unittest.mock import patch, MagicMock
from services.satusehat_service import SatusehatService

class TestSatusehatService:
    
    @patch('services.satusehat_service.requests.post')
    def test_fetch_token_success(self, mock_post):
        """Test OAuth2 token fetch"""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "token123"}
        mock_post.return_value = mock_response
        
        # Act
        token, error = SatusehatService.fetch_token()
        
        # Assert
        assert token == "token123"
        assert error is None
        mock_post.assert_called_once()
    
    @patch('services.satusehat_service.requests.post')
    def test_fetch_token_failure(self, mock_post):
        """Test OAuth2 token fetch failure"""
        # Arrange
        mock_post.side_effect = Exception("Connection error")
        
        # Act
        token, error = SatusehatService.fetch_token()
        
        # Assert
        assert token is None
        assert error is not None
    
    @patch('services.satusehat_service.requests.get')
    def test_fhir_get_success(self, mock_get):
        """Test FHIR GET request"""
        # Arrange
        url = "https://api.satusehat.kemkes.go.id/ImagingStudy"
        token = "token123"
        expected_data = {"resourceType": "Bundle"}
        
        mock_response = MagicMock()
        mock_response.json.return_value = expected_data
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Act
        data, status = SatusehatService.fhir_get(url, token)
        
        # Assert
        assert data == expected_data
        assert status == 200
        mock_get.assert_called_once()
    
    @patch.object(SatusehatService, 'fetch_token')
    @patch.object(SatusehatService, 'fhir_get')
    def test_get_imaging_study_id_found(self, mock_fhir, mock_token):
        """Test getting ImagingStudy ID successfully"""
        # Arrange
        mock_token.return_value = ("token123", None)
        mock_fhir.return_value = ({
            "resourceType": "Bundle",
            "entry": [{
                "resource": {
                    "resourceType": "ImagingStudy",
                    "id": "imaging123",
                    "subject": {"reference": "Patient/pat456"}
                }
            }]
        }, 200)
        
        # Act
        result, error = SatusehatService.get_imaging_study_id("ACC123")
        
        # Assert
        assert error is None
        assert result["imagingStudy_id"] == "imaging123"
        assert result["patient_reference"] == "Patient/pat456"
    
    @patch.object(SatusehatService, 'fetch_token')
    @patch.object(SatusehatService, 'fhir_get')
    def test_get_imaging_study_id_not_found(self, mock_fhir, mock_token):
        """Test ImagingStudy not found"""
        # Arrange
        mock_token.return_value = ("token123", None)
        mock_fhir.return_value = ({
            "resourceType": "Bundle",
            "entry": []
        }, 200)
        
        # Act
        result, error = SatusehatService.get_imaging_study_id("NOTFOUND")
        
        # Assert
        assert result is None
        assert error is not None
        assert "No ImagingStudy" in error
```

## Integration Tests

```python
# tests/test_routes_integration.py
import pytest
from app import app

@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

class TestDicomRoutes:
    
    @pytest.mark.integration
    @patch('routes.dicom_routes.PACSService.get_dicom_metadata')
    @patch('routes.dicom_routes.PACSService.download_wado')
    @patch('routes.dicom_routes.DicomService.send_to_router')
    def test_process_dicom_endpoint(self, mock_send, mock_download, 
                                     mock_metadata, client):
        """Test /process endpoint"""
        # Arrange
        mock_metadata.return_value = {
            "series": "1.2.3.4.5.1",
            "sop": "1.2.3.4.5.1.1"
        }
        
        # Act
        response = client.post('/api/dicom/process', json={
            'study': '1.2.3.4.5',
            'patientid': 'P123'
        })
        
        # Assert
        assert response.status_code == 200
        assert response.json['status'] == 'success'
    
    @pytest.mark.integration
    def test_api_documentation_available(self, client):
        """Test API docs endpoint"""
        # Act
        response = client.get('/api/docs')
        
        # Assert
        assert response.status_code == 200
        assert b'DICOM Gateway API' in response.data
```

## Running Tests

### Installation
```bash
pip install pytest pytest-cov pytest-mock
```

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_pacs_service.py -v
```

### Run with Coverage
```bash
pytest tests/ --cov=services --cov=routes --cov=core
```

### Run Integration Tests Only
```bash
pytest tests/ -v -m integration
```

## Test Structure

```
project/
├── app/
│   ├── app.py
│   ├── services/
│   │   └── ...
│   └── ...
│
└── tests/
    ├── __init__.py
    ├── conftest.py                # Shared fixtures
    ├── test_pacs_service.py       # PACS service tests
    ├── test_dicom_service.py      # DICOM service tests
    ├── test_satusehat_service.py  # SatuSehat service tests
    ├── test_routes_integration.py # Integration tests
    └── fixtures/
        ├── pacs_responses.json    # Mock PACS data
        ├── fhir_responses.json    # Mock FHIR data
        └── dicom_samples/         # Sample DICOM files
```

## Benefits of Testing Clean Architecture

| Aspect | Monolithic | Clean Architecture |
|--------|------------|-------------------|
| **Service Testing** | Hard to isolate | Easy, independent |
| **Mocking** | Complex, many deps | Simple, few deps |
| **Test Speed** | Slow, full setup | Fast, unit isolated |
| **Coverage** | Difficult to achieve | Easy to maintain |
| **Maintenance** | Tests break easily | Tests stable |

## CI/CD Integration

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt pytest pytest-cov
      - run: pytest tests/ --cov=services --cov=routes --cov=core
      - uses: codecov/codecov-action@v2
```

## Summary

With clean architecture:
- ✅ Services are independently testable
- ✅ Mocking is straightforward
- ✅ Tests are fast and isolated
- ✅ Code coverage is easier to maintain
- ✅ Test maintenance is reduced
- ✅ Integration testing is possible
- ✅ Quality assurance is improved
