//encounter POST {{base_url}}/Encounter
{
    "class": {
        "code": "AMB",
        "display": "ambulatory",
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode"
    },
    "id": "326ae5b2-6ca9-4678-b36a-5d5335843def",
    "identifier": [
        {
            "system": "http://sys-ids.kemkes.go.id/encounter/10000004",
            "value": "P20240001"
        }
    ],
    "location": [
        {
            "location": {
                "display": "Ruang 1A, Poliklinik Bedah Rawat Jalan Terpadu, Lantai 2, Gedung G",
                "reference": "Location/b017aa54-f1df-4ec2-9d84-8823815d7228"
            }
        }
    ],
    "meta": {
        "lastUpdated": "2022-08-09T02:45:03.503548+00:00",
        "versionId": "MTY2MDAxMzEwMzUwMzU0ODAwMA"
    },
    "participant": [
        {
            "individual": {
                "display": "Dokter Bronsig",
                "reference": "Practitioner/N10000001"
            },
            "type": [
                {
                    "coding": [
                        {
                            "code": "ATND",
                            "display": "attender",
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType"
                        }
                    ]
                }
            ]
        }
    ],
    "period": {
        "start": "2022-06-14T07:00:00+07:00"
    },
    "resourceType": "Encounter",
    "serviceProvider": {
        "reference": "Organization/10000004"
    },
    "status": "arrived",
    "statusHistory": [
        {
            "period": {
                "start": "2022-06-14T07:00:00+07:00"
            },
            "status": "arrived"
        }
    ],
    "subject": {
        "display": "Budi Santoso",
        "reference": "Patient/100000030009"
    }
}
//service request POST {{base_url}}/ServiceRequest
{
    "code": {
        "coding": [
            {
                "code": "11525-3",
                "display": "US for pregnancy",
                "system": "http://loinc.org"
            }
        ],
        "text": "Pemeriksaan USG"
    },
    "contained": [
        {
            "active": true,
            "birthDate": "1980-11-19",
            "gender": "female",
            "id": "100000030006",
            "identifier": [
                {
                    "system": "http://sys-ids.kemkes.go.id/mrn/10000004",
                    "value": "MR2301000234"
                }
            ],
            "name": [
                {
                    "text": "Jane Smith",
                    "use": "official"
                }
            ],
            "resourceType": "Patient"
        }
    ],
    "encounter": {
        "display": "Permintaan pemeriksaan USG untuk kehamilan",
        "reference": "Encounter/46d243f7-6137-4bb1-8f33-b746f408b94a"
    },
    "id": "71402eba-9c42-4c9d-9d2e-aa1e7531f344",
    "identifier": [
        {
            "system": "http://sys-ids.kemkes.go.id/servicerequest/10000004",
            "value": "00199"
        },
        {
            "system": "http://sys-ids.kemkes.go.id/acsn/10000004",
            "type": {
                "coding": [
                    {
                        "code": "ACSN",
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0203"
                    }
                ]
            },
            "use": "usual",
            "value": "00403"
        }
    ],
    "intent": "original-order",
    "meta": {
        "lastUpdated": "2023-11-23T10:57:31.974877+00:00",
        "versionId": "MTcwMDczNzA1MTk3NDg3NzAwMA"
    },
    "occurrenceDateTime": "2023-08-31T02:05:00+00:00",
    "orderDetail": [
        {
            "coding": [
                {
                    "code": "US",
                    "system": "http://dicom.nema.org/resources/ontology/DCM"
                }
            ],
            "text": "Modality Code: US"
        },
        {
            "coding": [
                {
                    "display": "CT0001",
                    "system": "http://sys-ids.kemkes.go.id/ae-title"
                }
            ]
        }
    ],
    "performer": [
        {
            "display": "Dokter Radiologist",
            "reference": "Practitioner/10012572188"
        }
    ],
    "priority": "routine",
    "reasonCode": [
        {
            "text": "Periksa rutin"
        }
    ],
    "requester": {
        "display": "Dokter Bambang Anta",
        "reference": "Practitioner/10012572188"
    },
    "resourceType": "ServiceRequest",
    "status": "active",
    "subject": {
        "reference": "Patient/100000030009"
    }
}
//get image GET {{base_url}}/ImagingStudy?identifier=http://sys-ids.kemkes.go.id/acsn/{{Org_id}}|{{ACSN}}

//observation POST {{base_url}}/Observation
{
    "resourceType": "Observation",
    "identifier": [
        {
            "system": "http://sys-ids.kemkes.go.id/observation/{{Org_id}}",
            "value": "O111111"
        }
    ],
    "status": "final",
    "category": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "imaging",
                    "display": "Imaging"
                }
            ]
        }
    ],
    "code": {
        "coding": [
            {
                "system": "http://loinc.org",
                "code": "24648-8",
                "display": "XR Chest PA upright"
            }
        ]
    },
    "subject": {
        "reference": "Patient/{{Patient_id}}",
        "display": "{{Patient_Name}}"
    },
    "encounter": {
        "reference": "Encounter/{{Encounter_id}}"
    },
    "effectiveDateTime": "2025-11-14T08:15:00+00:00",
    "issued": "2025-11-14T08:15:00+00:00",
    "performer": [
        {
            "reference": "Practitioner/10012572188",
            "display": "Dokter Radiologist"
        }
    ],
    "valueString": "Hasil Bacaan Dokter terkait Usg Ny Sonia adalah .....",
    "basedOn": [
        {
            "reference": "ServiceRequest/{{ServiceRequest_Rad}}"
        }
    ],
    "derivedFrom": [
        {
            "reference": "ImagingStudy/{{ImagingStudy_id}}"
        }
    ]
}
//diagnostic report POST {{base_url}}/DiagnosticReport
{
    "resourceType": "DiagnosticReport",
    "identifier": [
        {
            "system": "http://sys-ids.kemkes.go.id/diagnostic/{{Org_id}}/rad",
            "use": "official",
            "value": "5234352B"
        }
    ],
    "status": "final",
    "category": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                    "code": "RAD",
                    "display": "Radiology"
                }
            ]
        }
    ],
    "code": {
        "coding": [
            {
                "system": "http://loinc.org",
                "code": "11525-3",
                "display": "US for pregnancy"
            }
        ]
    },
    "subject": {
        "reference": "Patient/{{Patient_Ibu_ID}}"
    },
    "encounter": {
        "reference": "Encounter/{{Encounter_uuid}}"
    },
    "effectiveDateTime": "2025-11-14T05:00:00+00:00",
    "issued": "2025-11-14T05:00:00+00:00",
    "performer": [
        {
            "reference": "Practitioner/N10000001"
        },
        {
            "reference": "Organization/{{Org_id}}"
        }
    ],
    "imagingStudy": [
        {
            "reference": "ImagingStudy/{{ImagingStudy_id}}"
        }
    ],
    "result": [
        {
            "reference": "Observation/{{ObservationId}}"
        }
    ],
    "basedOn": [
        {
            "reference": "ServiceRequest/{{ServiceRequest_Rad}}"
        }
    ],
    "conclusion": "Ditemukan Janin hidup panjang 1.54 cm"
}