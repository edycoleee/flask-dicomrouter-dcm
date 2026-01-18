"""ServiceRequest FHIR Resource Builder"""
from core.config import Config


def build_servicereq_resource(data):
    """Build FHIR ServiceRequest resource from input data"""
    if data.get("resourceType") == "ServiceRequest":
        return data

    required = ["identifier_value", "noacsn", "subject_id", "encounter_id", "period_start"]
    for r in required:
        if not data.get(r):
            raise ValueError(f"Missing required field: {r}")

    org_id = Config.ORG_ID

    code_entry = {
        "system": "http://loinc.org",
        "code": data.get("coding_code") or "79103-8",
        "display": data.get("coding_display") or "CT Abdomen W contrast IV",
    }

    text_display = code_entry["display"]

    return {
        "resourceType": "ServiceRequest",
        "identifier": [
            {
                "system": f"http://sys-ids.kemkes.go.id/servicerequest/{org_id}",
                "value": data["identifier_value"],
            },
            {
                "use": "usual",
                "type": {
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "ACSN"}]
                },
                "system": f"http://sys-ids.kemkes.go.id/acsn/{org_id}",
                "value": data["noacsn"],
            },
        ],
        "status": "active",
        "intent": "original-order",
        "priority": "routine",
        "category": [
            {
                "coding": [
                    {"system": "http://snomed.info/sct", "code": "363679005", "display": "Imaging"}
                ]
            }
        ],
        "code": {"coding": [code_entry], "text": text_display},
        "orderDetail": [
            {
                "coding": [{"system": "http://dicom.nema.org/resources/ontology/DCM", "code": "DX"}],
                "text": "Modality Code: DX",
            },
            {
                "coding": [{"system": "http://sys-ids.kemkes.go.id/ae-title", "display": "DX0001"}]
            },
        ],
        "subject": {"reference": f"Patient/{data['subject_id']}"},
        "encounter": {
            "reference": f"Encounter/{data['encounter_id']}",
            "display": f"Permintaan pemeriksaan {text_display}",
        },
        "occurrenceDateTime": data["period_start"],
        "authoredOn": data["period_start"],
        "requester": {
            "reference": data.get("practitioner_id"),
            "display": data.get("practitioner_display"),
        },
        "performer": [
            {
                "reference": data.get("performer_id"),
                "display": data.get("performer_display"),
            }
        ],
        "reasonCode": [{"text": "Periksa rutin"}],
    }
