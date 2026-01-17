"""DICOM API Routes - Flask-RestX endpoints"""
import os
import requests
from datetime import datetime, timedelta
from flask import after_this_request, send_file, request
from flask_restx import Resource, Namespace, fields, reqparse
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from core.config import Config
from core.logger import setup_logger
from core.fhir import post_fhir
from services.dicom_service import DicomService
from services.pacs_service import PACSService
from services.imaging_service import ImagingService
from services.encounter_service import build_encounter_resource

logger = setup_logger()

# Create namespaces
dicom_ns = Namespace('dicom', description='DICOM Router / PACS Processing')
satset_ns = Namespace('satset', description='SatuSehat Integration Endpoints')

# Define upload parser for file upload
upload_parser = reqparse.RequestParser()
upload_parser.add_argument('file', type=FileStorage, location='files', required=True, help='DICOM file to upload')
upload_parser.add_argument('patientid', type=str, location='form', required=False, help='Patient ID to modify')
upload_parser.add_argument('accesionnum', type=str, location='form', required=False, help='Accession Number to modify')

# Define API models for DICOM
dicom_model = dicom_ns.model('DicomProcess', {
    'study': fields.String(required=False, description='Study UID'),
    'patientid': fields.String(required=False, description='Patient ID to modify'),
    'accesionnum': fields.String(required=False, description='Accession Number (can be used to find Study UID)')
})

# Define API models for SatuSehat
encounter_input = satset_ns.model(
    "EncounterInput",
    {
        "identifier_value": fields.String(description="No register / identifier value", example="RG2023I0000175"),
        "subject_id": fields.String(description="Patient ID (will be prefixed with 'Patient/')", example="P10443013727"),
        "subject_display": fields.String(description="Patient display name", example="MILA YASYFI TASBIHA"),
        "individual_id": fields.String(description="Practitioner ID (will be prefixed with 'Practitioner/')", example="10016869420"),
        "individual_display": fields.String(description="Practitioner display name", example="dr. ARIAWAN SETIADI, Sp.A"),
        "period_start": fields.String(description="Period start (ISO8601)", example="2025-08-01T05:57:41+00:00"),
        "period_end": fields.String(required=False, description="Period end (ISO8601, optional)", example="2025-08-01T06:07:41+00:00"),
        "location_id": fields.String(description="Location ID (will be prefixed with 'Location/')", example="ecff1c64-3f62-4469-b577-ea38f263b276"),
        "location_display": fields.String(description="Location display name", example="Ruang 1, Poliklinik Anak, Lantai 1, Gedung Poliklinik"),
    },
)


@dicom_ns.route('/process')
class ProcessDicom(Resource):
    """Unified DICOM Processing: Download All Instances -> Modify (Optional) -> Send to Router"""
    
    @dicom_ns.expect(dicom_model)
    def post(self):
        """
        Unified process endpoint supporting all scenarios:
        1. Process by Study UID
        2. Process by Accession Number
        3. Modify metadata (patient ID and/or accession number)
        4. Send ALL instances from the study to router
        
        Parameters:
            study: Study UID (optional)
            patientid: Patient ID to modify (optional)
            accesionnum: Accession Number - can be used to find Study UID or modify (optional)
            
        Returns:
            JSON with status, study_uid, instance counts, and router info
        """
        data = dicom_ns.payload
        study_uid = data.get('study')
        patient_id = data.get('patientid')
        accession = data.get('accesionnum')

        try:
            logger.info(f"[PROCESS] Starting unified DICOM processing")
            logger.info(f"  Study UID: {study_uid}, Patient ID: {patient_id}, Accession: {accession}")
            
            # =====================================================
            # 1 & 2. Determine Study UID
            # =====================================================
            if study_uid:
                # Validate study exists
                logger.info(f"[PROCESS] Validating Study UID: {study_uid}")
                try:
                    instances = PACSService.get_all_instances(study_uid)
                    if not instances:
                        logger.warning(f"[PROCESS] Study UID has no instances: {study_uid}")
                        return {
                            "status": "error",
                            "message": "Study UID tidak memiliki instance"
                        }, 404
                except Exception as e:
                    logger.warning(f"[PROCESS] Study UID not found: {study_uid} - {str(e)}")
                    return {
                        "status": "error",
                        "message": "Study UID tidak ditemukan di PACS"
                    }, 404
            else:
                # Study kosong → cari via Accession Number
                if not accession:
                    logger.warning(f"[PROCESS] Neither Study UID nor Accession Number provided")
                    return {
                        "status": "error",
                        "message": "Study UID dan Accession Number kosong - satu diantaranya harus diberikan"
                    }, 400

                logger.info(f"[PROCESS] Finding Study UID by Accession: {accession}")
                study_uid, err = PACSService.get_study_uid_by_accession(accession)
                if err:
                    logger.warning(f"[PROCESS] Accession not found: {accession} - {err}")
                    return {
                        "status": "error",
                        "message": err
                    }, 404

                instances = PACSService.get_all_instances(study_uid)
                if not instances:
                    logger.warning(f"[PROCESS] Study found but no instances: {study_uid}")
                    return {
                        "status": "error",
                        "message": "Study ditemukan tapi tidak ada instance"
                    }, 404

            logger.info(f"[PROCESS] Found {len(instances)} instances for Study UID: {study_uid}")

            # =====================================================
            # 3–8. Download, Modify (opsional), Send (LOOP)
            # =====================================================
            success_count = 0
            failed_count = 0
            failed_instances = []

            for idx, inst in enumerate(instances):
                local_path = os.path.join(
                    Config.TEMP_DIR, f"proc_{study_uid}_{idx}.dcm"
                )

                try:
                    logger.info(f"[PROCESS] Processing instance {idx + 1}/{len(instances)}")
                    
                    # 3. Download WADO (per SOP)
                    logger.debug(f"[PROCESS] Downloading instance {idx} (series: {inst['series']}, sop: {inst['sop']})")
                    PACSService.download_wado(study_uid, inst, local_path)

                    # 4–7. Modify DICOM (bersyarat)
                    if patient_id or accession:
                        logger.debug(f"[PROCESS] Modifying DICOM tags - Patient ID: {patient_id}, Accession: {accession}")
                        DicomService.modify_dicom(
                            local_path,
                            patient_id=patient_id if patient_id else None,
                            acc_num=accession if accession else None,
                        )

                    # 8. Kirim ke Router
                    logger.debug(f"[PROCESS] Sending instance {idx} to router ({Config.ROUTER_IP}:{Config.ROUTER_PORT})")
                    DicomService.send_to_router(local_path)
                    success_count += 1
                    logger.info(f"[PROCESS] Instance {idx + 1} sent successfully")

                except Exception as e:
                    failed_count += 1
                    failed_instances.append({"instance": idx, "error": str(e)})
                    logger.error(f"[PROCESS] Failed to process instance {idx}: {str(e)}")

                finally:
                    # Cleanup per file
                    if os.path.exists(local_path):
                        os.remove(local_path)

            logger.info(f"[PROCESS] Completed - Success: {success_count}/{len(instances)}, Failed: {failed_count}")
            
            return {
                "status": "success" if success_count > 0 else "partial_error",
                "study_uid": study_uid,
                "total_instance": len(instances),
                "sent_instance": success_count,
                "failed_instance": failed_count,
                "failed_details": failed_instances if failed_instances else None,
                "patient_modified": bool(patient_id),
                "accession_modified": bool(accession),
                "router": f"{Config.ROUTER_IP}:{Config.ROUTER_PORT}",
            }, 200 if success_count > 0 else 207  # 207 Multi-Status if partial success

        except Exception as e:
            logger.error(f"[PROCESS] Unexpected error: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }, 500



@dicom_ns.route('/upload')
class UploadDicom(Resource):
    """Upload local DICOM file -> Modify -> Send to Router"""
    
    @dicom_ns.doc(parser=upload_parser)
    def post(self):
        """Upload and process DICOM file"""
        args = upload_parser.parse_args()
        
        file = args['file']
        if not file or file.filename == '':
            return {"status": "error", "message": "No file selected"}, 400
        
        filename = secure_filename(file.filename)
        temp_path = os.path.join(Config.TEMP_DIR, f"up_{filename}")
        
        try:
            file.save(temp_path)
            logger.info(f"[UPLOAD] File uploaded: {filename}")
            
            patientid = args.get('patientid')
            accesionnum = args.get('accesionnum')
            
            # Modify DICOM tags if provided
            if patientid or accesionnum:
                logger.info(f"[UPLOAD] Modifying tags - Patient ID: {patientid}, Accession: {accesionnum}")
                DicomService.modify_dicom(temp_path, patientid, accesionnum)
            
            # Send to router
            logger.info(f"[UPLOAD] Sending file to router ({Config.ROUTER_IP}:{Config.ROUTER_PORT})")
            DicomService.send_to_router(temp_path)
            
            logger.info(f"[UPLOAD] File {filename} successfully sent to router")
            return {
                "status": "success",
                "file": filename,
                "message": f"File {filename} berhasil diunggah dan dikirim ke Router"
            }, 200
        except Exception as e:
            logger.error(f"[UPLOAD] Process failed: {str(e)}")
            return {"status": "error", "message": str(e)}, 500
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


@dicom_ns.route('/download/<study_uid>')
class DownloadDicom(Resource):
    """Download DICOM file to user's computer"""
    
    def get(self, study_uid):
        """Download DICOM file by Study UID"""
        local_path = os.path.join(Config.TEMP_DIR, f"dl_{study_uid}.dcm")
        
        @after_this_request
        def cleanup(response):
            if os.path.exists(local_path):
                os.remove(local_path)
            return response

        try:
            meta = PACSService.get_dicom_metadata(study_uid)
            PACSService.download_wado(study_uid, meta, local_path)
            return send_file(
                local_path,
                as_attachment=True,
                download_name=f"{study_uid}.dcm"
            )
        except Exception as e:
            return {"error": str(e)}, 500


@satset_ns.route('/encounter')
class EncounterCreate(Resource):
    """Create Encounter in SatuSehat FHIR Server"""
    
    @satset_ns.expect(encounter_input, validate=False)
    def post(self):
        """
        Create a new Encounter resource in SatuSehat
        
        Parameters:
            identifier_value: No register / identifier value
            subject_id: Patient ID (will be prefixed with 'Patient/')
            subject_display: Patient display name
            individual_id: Practitioner ID (will be prefixed with 'Practitioner/')
            individual_display: Practitioner display name
            period_start: Period start (ISO8601 format, required)
            period_end: Period end (ISO8601 format, optional, defaults to period_start + 10 minutes)
            location_id: Location ID (will be prefixed with 'Location/')
            location_display: Location display name
            
        Returns:
            JSON with encounter_id and created resource
        """
        try:
            data = request.get_json(silent=True) or {}
            
            logger.info(f"[SATUSEHAT] Creating Encounter with identifier: {data.get('identifier_value')}")
            
            # Build FHIR Encounter resource
            encounter = build_encounter_resource(data)
            
            # Get access token
            from core.fhir import fetch_token
            token, err = fetch_token()
            if err:
                logger.error(f"[SATUSEHAT] Authentication failed: {err}")
                return {"status": "error", "message": f"Authentication failed: {err}"}, 502
            
            # POST to SatuSehat FHIR server
            url = Config.BASE_URL.rstrip("/") + "/Encounter"
            logger.debug(f"[SATUSEHAT] POSTing to: {url}")
            
            enc_resp, status_code = post_fhir(url, token, encounter)
            
            if status_code >= 300:
                logger.error(f"[SATUSEHAT] Failed to create Encounter: {enc_resp}")
                return enc_resp, status_code
            
            # Extract Encounter ID from response
            encounter_id = enc_resp.get("id")
            if not encounter_id:
                logger.warning(f"[SATUSEHAT] Encounter created but no ID returned")
                return {"error": "Encounter created but no ID returned", "detail": enc_resp}, 500
            
            logger.info(f"[SATUSEHAT] Encounter created successfully with ID: {encounter_id}")
            
            return {
                "status": "success",
                "encounter_id": encounter_id,
                "resource": enc_resp
            }, 201
            
        except ValueError as e:
            logger.error(f"[SATUSEHAT] Validation error: {str(e)}")
            return {"status": "error", "message": str(e)}, 400
        except Exception as e:
            logger.error(f"[SATUSEHAT] Unexpected error: {str(e)}")
            return {"status": "error", "message": str(e)}, 500



@satset_ns.route('/imageid/<string:acsn>')
@satset_ns.doc(params={'acsn': 'Accession Number dari PACS/SatuSehat'})
class ImageId(Resource):
    """Get ImagingStudy ID from SatuSehat based on Accession Number"""
    
    def get(self, acsn):
        """Retrieve ImagingStudy ID from SatuSehat"""
        result, err = ImagingService.get_imaging_study_id(acsn)
        
        if err:
            logger.error(f"[SATUSEHAT] SatuSehat lookup failed: {err}")
            return {
                "status": "error",
                "message": err
            }, 502 if "Auth" in err else 404
        
        logger.info(f"[SATUSEHAT] ImagingStudy found: {result['imagingStudy_id']}")
        return {
            "status": "success",
            "imagingStudy_id": result['imagingStudy_id'],
            "patient_reference": result['patient_reference']
        }, 200
