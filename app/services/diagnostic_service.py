"""DiagnosticReport FHIR Resource Builder"""
from core.config import Config


def build_diagnostic_resource(data):
    """Build FHIR DiagnosticReport resource from input data"""
    if data.get("resourceType") == "DiagnosticReport":
        return data

    identifier_value = data.get("identifier_value") or data.get("identifier")
    coding_code = data.get("codind_code") or data.get("coding_code") or data.get("code")
    coding_display = data.get("coding_display") or data.get("codingText")

    subject_id = data.get("subject_id")
    encounter_id = data.get("encounter_id")
    period_start = data.get("period_start")

    performer_id = data.get("performer_id")

    imaging_study_id = data.get("imaging_study_id")
    observation_id = data.get("observation_id")
    service_request_id = data.get("service_request_id")

    conclusion_text = data.get("conclusion_text") or data.get("conclusion")

    org_id = Config.ORG_ID

    # Validation
    if not identifier_value or not subject_id or not encounter_id or not period_start:
        raise ValueError("Missing required fields: identifier_value, subject_id, encounter_id, period_start")

    code_entry = {
        "system": "http://loinc.org",
        "code": coding_code or "79103-8",
        "display": coding_display or "Imaging",
    }

    drep = {
        "resourceType": "DiagnosticReport",
        "identifier": [
            {
                "system": f"http://sys-ids.kemkes.go.id/diagnostic/{org_id}/rad",
                "use": "official",
                "value": identifier_value,
            }
        ],
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                        "code": "RAD",
                        "display": "Radiology",
                    }
                ]
            }
        ],
        "code": {"coding": [code_entry]},
        "subject": {"reference": f"Patient/{subject_id}"},
        "encounter": {"reference": f"Encounter/{encounter_id}"},
        "effectiveDateTime": period_start,
        "issued": period_start,
        "performer": [
            {"reference": f"Practitioner/{performer_id}"},
            {"reference": f"Organization/{org_id}"},
        ],
        "imagingStudy": [{"reference": f"ImagingStudy/{imaging_study_id}"}] if imaging_study_id else [],
        "result": [{"reference": f"Observation/{observation_id}"}] if observation_id else [],
        "basedOn": [{"reference": f"ServiceRequest/{service_request_id}"}] if service_request_id else [],
        "conclusion": conclusion_text or "",
    }

    return drep
