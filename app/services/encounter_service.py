"""Encounter Service - Handles Encounter resource building for SatuSehat FHIR"""
from datetime import datetime, timedelta
from core.config import Config
from core.logger import setup_logger

logger = setup_logger()


def build_encounter_resource(data):
    """
    Build FHIR Encounter resource from input data.
    
    Args:
        data (dict): Input data containing encounter details
            - identifier_value: No register / identifier value
            - subject_id: Patient ID
            - subject_display: Patient display name
            - individual_id: Practitioner ID
            - individual_display: Practitioner display name
            - period_start: Period start (ISO8601)
            - period_end: Period end (ISO8601, optional)
            - location_id: Location ID
            - location_display: Location display name
    
    Returns:
        dict: FHIR Encounter resource
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    # If already a proper FHIR resource, return as-is
    if data.get("resourceType") == "Encounter":
        return data

    period_start = data.get("period_start")
    if not period_start:
        raise ValueError("period_start is required")

    try:
        dt_start = datetime.fromisoformat(period_start)
    except:
        raise ValueError("period_start must be ISO8601")

    # Default period_end to 10 minutes after start
    period_end = data.get("period_end") or (dt_start + timedelta(minutes=10)).isoformat()

    org_id = Config.ORG_ID

    return {
        "resourceType": "Encounter",
        "identifier": [
            {
                "system": f"http://sys-ids.kemkes.go.id/encounter/{org_id}",
                "value": data.get("identifier_value"),
            }
        ],
        "status": "arrived",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "AMB",
            "display": "ambulatory",
        },
        "subject": {
            "reference": f"Patient/{data.get('subject_id')}",
            "display": data.get("subject_display"),
        },
        "participant": [
            {
                "type": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                                "code": "ATND",
                                "display": "attender",
                            }
                        ]
                    }
                ],
                "individual": {
                    "reference": f"Practitioner/{data.get('individual_id')}",
                    "display": data.get("individual_display"),
                },
            }
        ],
        "period": {"start": period_start, "end": period_end},
        "location": [
            {
                "location": {
                    "reference": f"Location/{data.get('location_id')}",
                    "display": data.get("location_display"),
                }
            }
        ],
        "statusHistory": [{"status": "arrived", "period": {"start": period_start, "end": period_end}}],
        "serviceProvider": {"reference": f"Organization/{org_id}"},
    }
