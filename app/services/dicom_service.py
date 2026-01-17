"""DICOM Processing Service - Handles DICOM modification and routing"""
import os
import subprocess
from core.config import Config

class DicomService:
    """Service for DICOM processing and modification."""
    
    @staticmethod
    def modify_dicom(file_path, patient_id=None, acc_num=None):
        """
        Edit DICOM tags using dcmodify.
        
        Args:
            file_path (str): Path to DICOM file
            patient_id (str, optional): Patient ID to set
            acc_num (str, optional): Accession Number to set
            
        Raises:
            Exception: If dcmodify command fails
        """
        cmd = ["dcmodify", "--ignore-errors"]
        if patient_id:
            cmd.extend(["-i", f"(0010,0020)={patient_id}"])
        if acc_num:
            cmd.extend(["-i", f"(0008,0050)={acc_num}"])
        cmd.append(file_path)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"dcmodify error: {result.stderr}")
        
        # Remove backup file created by dcmodify
        backup_path = f"{file_path}.bak"
        if os.path.exists(backup_path):
            os.remove(backup_path)

    @staticmethod
    def send_to_router(file_path):
        """
        Send DICOM file to Router using storescu.
        
        Args:
            file_path (str): Path to DICOM file to send
            
        Raises:
            Exception: If storescu command fails
        """
        cmd = [
            "storescu",
            "-v",
            "--propose-lossless",
            "-aec", Config.ROUTER_AET,
            Config.ROUTER_IP,
            Config.ROUTER_PORT,
            file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if "Received Store Response (Success)" not in (result.stdout + result.stderr):
            raise Exception(f"StoreSCU Failed: {result.stderr}")
