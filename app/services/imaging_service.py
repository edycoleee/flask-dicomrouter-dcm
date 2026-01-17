"""Imaging Study Service - Handles ImagingStudy retrieval from SatuSehat FHIR"""
from core.config import Config
from core.fhir import fetch_token, fhir_get


class ImagingService:
    """Service for retrieving ImagingStudy data from SatuSehat FHIR API."""
    
    @staticmethod
    def get_imaging_study_id(accession_num):
        """
        Get ImagingStudy ID from SatuSehat based on Accession Number.
        
        Args:
            accession_num (str): Accession Number
            
        Returns:
            tuple: (dict with imaging_study_id and patient_reference, error message or None)
        """
        token, err = fetch_token()
        if err:
            return None, err
        
        identifier_system = f"http://sys-ids.kemkes.go.id/acsn/{Config.ORG_ID}"
        url = f"{Config.BASE_URL}/ImagingStudy?identifier={identifier_system}|{accession_num}"
        
        data, status = fhir_get(url, token)
        
        if status != 200:
            return None, str(data)

        if data.get("resourceType") == "Bundle":
            entries = data.get("entry") or []
            for e in entries:
                res = e.get("resource") or {}
                if res.get("resourceType") == "ImagingStudy":
                    return {
                        "imagingStudy_id": res.get("id"),
                        "patient_reference": res.get("subject", {}).get("reference")
                    }, None

        return None, "No ImagingStudy found for this Accession Number"
