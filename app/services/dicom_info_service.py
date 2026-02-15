"""DICOM Information Service - Handles DICOM study queries and downloads"""
import os
import requests
from core.config import Config
from core.logger import setup_logger

logger = setup_logger()


class DicomInfoService:
    """Service for querying and downloading DICOM studies from PACS."""
    
    @staticmethod
    def get_study_by_accession(accession_number):
        """
        Get DICOM study information by accession number.
        
        Args:
            accession_number (str): Accession number to query
            
        Returns:
            dict: Study information from PACS
            
        Raises:
            Exception: If PACS query fails
        """
        # Build URL - DCM4CHEE_URL already includes full path to AET
        url = f"{Config.DCM4CHEE_URL}/rs/studies"
        params = {"AccessionNumber": accession_number}
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            studies = response.json()
            if not studies:
                raise Exception(f"No study found for accession number: {accession_number}")
            
            logger.info(f"Found {len(studies)} study(ies) for accession: {accession_number}")
            return studies[0] if len(studies) == 1 else studies
            
        except requests.RequestException as e:
            logger.error(f"Failed to get study: {e}")
            raise Exception(f"PACS query failed: {str(e)}")
    
    @staticmethod
    def get_thumbnail_by_accession(accession_number):
        """
        Get thumbnail image for a study by accession number.
        
        Args:
            accession_number (str): Accession number to query
            
        Returns:
            bytes: Thumbnail image data
            
        Raises:
            Exception: If thumbnail retrieval fails
        """
        # First get study UID
        study = DicomInfoService.get_study_by_accession(accession_number)
        
        # Extract Study Instance UID from tag 0020000D
        study_uid = study.get("0020000D", {}).get("Value", [None])[0]
        if not study_uid:
            raise Exception("Study UID not found in DICOM response")
        
        # Get thumbnail - DCM4CHEE_URL already includes full path to AET
        url = f"{Config.DCM4CHEE_URL}/rs/studies/{study_uid}/thumbnail"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            logger.info(f"Retrieved thumbnail for study: {study_uid}")
            return response.content
            
        except requests.RequestException as e:
            logger.error(f"Failed to get thumbnail: {e}")
            raise Exception(f"Thumbnail retrieval failed: {str(e)}")
    
    @staticmethod
    def download_study_by_accession(accession_number, output_path=None):
        """
        Download DICOM study by accession number to local file.
        
        Args:
            accession_number (str): Accession number to download
            output_path (str, optional): Path to save the file. If None, saves to TEMP_DIR
            
        Returns:
            str: Path to downloaded file
            
        Raises:
            Exception: If download fails
        """
        # First get study UID
        study = DicomInfoService.get_study_by_accession(accession_number)
        
        # Extract Study Instance UID from tag 0020000D
        study_uid = study.get("0020000D", {}).get("Value", [None])[0]
        if not study_uid:
            raise Exception("Study UID not found in DICOM response")
        
        # Prepare output path
        if not output_path:
            Config.init_app()  # Ensure temp dir exists
            output_path = os.path.join(Config.TEMP_DIR, f"{accession_number}.zip")
        
        # Download study - DCM4CHEE_URL already includes full path to AET
        url = f"{Config.DCM4CHEE_URL}/rs/studies/{study_uid}"
        
        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            # Write to file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(output_path)
            logger.info(f"Downloaded study {study_uid} to {output_path} ({file_size} bytes)")
            
            return output_path
            
        except requests.RequestException as e:
            logger.error(f"Failed to download study: {e}")
            raise Exception(f"Study download failed: {str(e)}")
        except IOError as e:
            logger.error(f"Failed to write file: {e}")
            raise Exception(f"File write failed: {str(e)}")
