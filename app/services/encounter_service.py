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
            - practitioner_id: Practitioner ID
            - practitioner_display: Practitioner display name
            - period_start: Period start (ISO8601)
            - period_end: Period end (ISO8601)
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
    
    period_end = data.get("period_end")
    if not period_end:
        raise ValueError("period_end is required")

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
                    "reference": f"Practitioner/{data.get('practitioner_id')}",
                    "display": data.get("practitioner_display"),
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
