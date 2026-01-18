"""Observation FHIR Resource Builder"""
from core.config import Config


def build_observation_resource(data):
    """Build FHIR Observation resource from input data"""
    if data.get("resourceType") == "Observation":
        return data

    identifier_value = data.get("identifier_value") or data.get("identifier")
    coding_code = data.get("codind_code") or data.get("coding_code") or data.get("code")
    coding_display = data.get("coding_display") or data.get("codingText")

    subject_id = data.get("subject_id")
    subject_display = data.get("subject_display")

    encounter_id = data.get("encounter_id")
    period_start = data.get("period_start")

    performer_id = data.get("performer_id")
    performer_display = data.get("performer_display")
    performer_value = data.get("performer_value") or data.get("valueString")

    service_request_id = data.get("service_request_id")
    imaging_study_id = data.get("imaging_study_id")

    org_id = Config.ORG_ID

    # Validation
    if not identifier_value or not subject_id or not encounter_id or not period_start:
        raise ValueError("Missing required fields: identifier_value, subject_id, encounter_id, period_start")

    code_entry = {
        "system": "http://loinc.org",
        "code": coding_code or "79103-8",
        "display": coding_display or "Imaging result",
    }

    obs = {
        "resourceType": "Observation",
        "identifier": [
            {
                "system": f"http://sys-ids.kemkes.go.id/observation/{org_id}",
                "value": identifier_value,
            }
        ],
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "imaging",
                        "display": "Imaging",
                    }
                ]
            }
        ],
        "code": {"coding": [code_entry]},
        "subject": {
            "reference": f"Patient/{subject_id}",
            "display": subject_display,
        },
        "encounter": {"reference": f"Encounter/{encounter_id}"},
        "effectiveDateTime": period_start,
        "issued": period_start,
        "performer": [
            {
                "reference": f"Practitioner/{performer_id}",
                "display": performer_display,
            }
        ],
        "valueString": performer_value,
        "basedOn": [{"reference": f"ServiceRequest/{service_request_id}"}] if service_request_id else [],
        "derivedFrom": [{"reference": f"ImagingStudy/{imaging_study_id}"}] if imaging_study_id else [],
    }

    return obs
