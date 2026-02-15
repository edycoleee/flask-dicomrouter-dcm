"""PACS (DCM4CHEE) Service - Handles DICOM file operations"""
import os
import uuid
import requests
from core.config import Config

class PACSService:
    """Service for PACS (DCM4CHEE) operations."""

    @staticmethod
    def _get_aets_base_url():
        base = (Config.DCM4CHEE_URL or "").rstrip("/")
        if not base:
            raise Exception("DCM4CHEE_URL belum dikonfigurasi")

        if "/aets/" in base:
            return base

        if Config.PACS_AET:
            return f"{base}/aets/{Config.PACS_AET}"

        return base

    @staticmethod
    def _parse_response(resp):
        try:
            return resp.json(), resp.status_code
        except ValueError:
            text = (resp.text or "").strip()
            return {"raw": text}, resp.status_code

    @staticmethod
    def _get_auth():
        if Config.PACS_USER and Config.PACS_PASSWORD:
            return (Config.PACS_USER, Config.PACS_PASSWORD)
        return None
    
    @staticmethod
    def get_dicom_metadata(study_uid):
        """
        Fetch Series and SOP UID from PACS.
        
        Args:
            study_uid (str): Study UID
            
        Returns:
            dict: Dictionary with 'series' and 'sop' keys
            
        Raises:
            Exception: If request fails
        """
        url = f"{Config.DCM4CHEE_URL}/rs/studies/{study_uid}/metadata"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return {
            "series": data[0]["0020000E"]["Value"][0],
            "sop": data[0]["00080018"]["Value"][0]
        }

    @staticmethod
    def download_wado(study_uid, meta, target_path):
        """
        Download original DICOM file using WADO protocol.
        
        Args:
            study_uid (str): Study UID
            meta (dict): Dictionary with 'series' and 'sop' keys
            target_path (str): Local file path to save DICOM
            
        Raises:
            Exception: If download fails
        """
        params = {
            "requestType": "WADO",
            "studyUID": study_uid,
            "seriesUID": meta['series'],
            "objectUID": meta['sop'],
            "contentType": "application/dicom"
        }
        with requests.get(
            f"{Config.DCM4CHEE_URL}/wado", 
            params=params, 
            stream=True
        ) as r:
            r.raise_for_status()
            with open(target_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

    @staticmethod
    def get_all_instances(study_uid):
        """
        Get all instances (series/SOP pairs) from a study.
        
        Args:
            study_uid (str): Study UID
            
        Returns:
            list: List of dicts with 'series' and 'sop' keys
            
        Raises:
            Exception: If metadata retrieval fails
        """
        url = f"{Config.DCM4CHEE_URL}/rs/studies/{study_uid}/metadata"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        instances = []
        for item in data:
            instances.append({
                "series": item["0020000E"]["Value"][0],
                "sop": item["00080018"]["Value"][0],
            })

        return instances

    @staticmethod
    def get_study_uid_by_accession(acc_num):
        """
        Find Study UID based on Accession Number.
        
        Args:
            acc_num (str): Accession Number
            
        Returns:
            tuple: (study_uid, error_message or None)
        """
        url = f"{Config.DCM4CHEE_URL}/rs/studies?AccessionNumber={acc_num}"

        try:
            resp = requests.get(url, timeout=10)

            # If PACS returns HTML error → don't parse JSON
            if resp.status_code == 404 or resp.text.strip() == "":
                return None, "Study tidak ditemukan"

            try:
                studies = resp.json()
            except Exception:
                return None, "Response PACS tidak valid (bukan JSON)"

            if not studies:
                return None, "Study tidak ditemukan"

            study_uid = studies[0]["0020000D"]["Value"][0]
            return study_uid, None

        except Exception as e:
            return None, str(e)

    @staticmethod
    def find_by_accession(acc_num):
        """
        Find Study, Series, SOP based on Accession Number.
        
        Args:
            acc_num (str): Accession Number
            
        Returns:
            tuple: (dict with study/series/sop, error_message or None)
        """
        url = f"{Config.DCM4CHEE_URL}/rs/studies?AccessionNumber={acc_num}"

        try:
            resp = requests.get(url, timeout=10)

            # If PACS returns HTML error → don't parse JSON
            if resp.status_code == 404 or resp.text.strip() == "":
                return None, "Study tidak ditemukan"

            try:
                studies = resp.json()
            except Exception:
                return None, "Response PACS tidak valid (bukan JSON)"

            if not studies:
                return None, "Study tidak ditemukan"

            study_uid = studies[0]["0020000D"]["Value"][0]

            # Get full metadata
            meta_url = f"{Config.DCM4CHEE_URL}/rs/studies/{study_uid}/metadata"
            meta_resp = requests.get(meta_url, timeout=10)

            try:
                meta = meta_resp.json()
            except Exception:
                return None, "Metadata PACS tidak valid"

            series_uid = meta[0]["0020000E"]["Value"][0]
            sop_uid = meta[0]["00080018"]["Value"][0]

            return {
                "study": study_uid,
                "series": series_uid,
                "sop": sop_uid
            }, None

        except Exception as e:
            return None, str(e)

    @staticmethod
    def upload_study(file_path):
        """
        Upload DICOM file to DCM4CHEE (STOW-RS).

        Args:
            file_path (str): Path to DICOM file

        Returns:
            tuple: (response_body, status_code)
        """
        aets_base = PACSService._get_aets_base_url()
        url = f"{aets_base}/rs/studies"

        boundary = f"dicom-{uuid.uuid4().hex}"
        headers = {
            "Content-Type": f"multipart/related; type=\"application/dicom\"; boundary={boundary}"
        }

        with open(file_path, "rb") as f:
            dicom_bytes = f.read()

        body = (
            f"--{boundary}\r\n"
            "Content-Type: application/dicom\r\n\r\n"
        ).encode("utf-8") + dicom_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

        resp = requests.post(url, data=body, headers=headers, timeout=60, auth=PACSService._get_auth())
        return PACSService._parse_response(resp)

    @staticmethod
    def delete_study(study_uid):
        """
        Delete DICOM study from DCM4CHEE.

        Args:
            study_uid (str): Study UID

        Returns:
            tuple: (response_body, status_code)
        """
        aets_base = PACSService._get_aets_base_url()
        url = f"{aets_base}/rs/studies/{study_uid}"
        resp = requests.delete(url, timeout=30, auth=PACSService._get_auth())
        return PACSService._parse_response(resp)
