// Show alert message
function showAlert(message, type = "info") {
    const box = document.getElementById('alertBox');
    box.className = `alert alert-${type}`;
    box.textContent = message;
    box.classList.remove('d-none');

    // Auto hide after 4 seconds
    setTimeout(() => {
        box.classList.add('d-none');
    }, 4000);
}

// Initialize log console
const logConsole = document.getElementById('logConsole');
const loadingModalEl = document.getElementById('loadingModal');
const loadingModal = bootstrap.Modal.getOrCreateInstance(loadingModalEl);

// Add log entry
function addLog(message, type = 'info') {
    const time = new Date().toLocaleTimeString('id-ID');
    let color = "#00ff00";
    if (type === 'error') color = "#ff4d4d";
    if (type === 'warning') color = "#ffcc00";

    const entry = document.createElement('div');
    entry.className = "log-entry";
    entry.style.color = color;
    entry.innerHTML = `<span class="timestamp">[${time}]</span> >> ${message}`;
    logConsole.appendChild(entry);
    logConsole.scrollTop = logConsole.scrollHeight;
}

// Search SatuSehat by Accession Number
async function searchSatuSehat() {
    const acsn = document.getElementById('ssAccNo').value;
    const resBox = document.getElementById('ssResult');
    if (!acsn) return alert("Masukkan Accession Number");

    addLog(`[SATUSEHAT] Mencari data untuk Accession: ${acsn}`, 'warning');
    resBox.style.display = 'none';

    try {
        const r = await fetch(`/api/satset/imageid/${acsn}`);
        const d = await r.json();
        if (r.ok) {
            document.getElementById('resId').innerText = d.imagingStudy_id;
            document.getElementById('resSub').innerText = d.patient_reference || '-';
            resBox.style.display = 'block';
            addLog(`[SUCCESS] ImagingStudy ID ditemukan: ${d.imagingStudy_id}`);
        } else {
            addLog(`[FAILED] Data tidak ditemukan di SatuSehat.`, 'error');
            alert("Data tidak ditemukan di SatuSehat.");
        }
    } catch (e) {
        addLog(`[ERROR] Koneksi SatuSehat bermasalah.`, 'error');
        alert("Terjadi kesalahan koneksi.");
    }
}

// Copy ImagingStudy ID to clipboard
function copyToClipboard() {
    const id = document.getElementById('resId').innerText;
    navigator.clipboard.writeText(id).then(() => {
        alert("ID Berhasil disalin!");
    });
}

// ========== FORM HANDLERS ==========

// Process Form
document.getElementById('formProcess').addEventListener('submit', async (e) => {
    e.preventDefault();

    const study = document.getElementById('proc-study').value.trim();
    const accessionLookup = document.getElementById('proc-acc-lookup').value.trim();
    const patientId = document.getElementById('proc-pid').value.trim();
    const accessionModify = document.getElementById('proc-acc-modify').value.trim();

    // Validation: at least one input required (study OR accession)
    if (!study && !accessionLookup) {
        showAlert("Masukkan Study UID ATAU Accession Number terlebih dahulu", "danger");
        addLog(`[VALIDATION] Error: Study UID dan Accession Number tidak boleh kosong bersama`, 'error');
        return;
    }

    const payload = {
        study: study || undefined,
        patientid: patientId || undefined,
        accesionnum: accessionLookup || accessionModify || undefined
    };

    // Remove undefined values
    Object.keys(payload).forEach(key => payload[key] === undefined && delete payload[key]);

    const displayIdentifier = study || accessionLookup;
    showAlert(`Memproses: ${displayIdentifier} (Unified Endpoint)`, "warning");
    addLog(`[UNIFIED-PROCESS] Mulai proses dengan input: Study=${study || 'N/A'}, Accession=${accessionLookup || accessionModify || 'N/A'}`, 'warning');

    try {
        const resp = await fetch('/api/dicom/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        let res = {};
        try {
            res = await resp.json();
        } catch {
            res = { message: "Invalid JSON response" };
        }

        if (resp.ok || resp.status === 207) {
            // 200 = full success, 207 = partial success
            const successCount = res.sent_instance || 0;
            const totalCount = res.total_instance || 0;
            const failedCount = res.failed_instance || 0;

            if (resp.status === 207) {
                showAlert(`Berhasil parsial: ${successCount}/${totalCount} instance terkirim. ${failedCount} gagal.`, "warning");
                addLog(`[PARTIAL-SUCCESS] Terkirim: ${successCount}/${totalCount} instances`, 'warning');
                if (res.failed_details && res.failed_details.length > 0) {
                    res.failed_details.forEach(f => {
                        addLog(`  - Instance ${f.instance}: ${f.error}`, 'warning');
                    });
                }
            } else {
                showAlert(`Sukses! ${totalCount} instance terkirim ke Router`, "success");
                addLog(`[SUCCESS] Semua ${totalCount} instances berhasil terkirim!`, 'info');
            }

            addLog(`[STATS] Total: ${totalCount}, Terkirim: ${successCount}, Gagal: ${failedCount}`, 'info');
            if (res.patient_modified) addLog(`[MODIFIED] Patient ID di-ubah`, 'info');
            if (res.accession_modified) addLog(`[MODIFIED] Accession Number di-ubah`, 'info');
        } else {
            showAlert(`Gagal memproses: ${res.message}`, "danger");
            addLog(`[FAILED] Server Response: ${res.message || 'Error'}`, 'error');
        }

    } catch (err) {
        showAlert(`Network Error: ${err}`, "danger");
        addLog(`[ERROR] Gagal menghubungi API: ${err.message}`, 'error');
    }
});

// Upload Form
document.getElementById('formUpload').addEventListener('submit', async (e) => {
    e.preventDefault();

    const fileInput = document.getElementById('upload-file');
    const patientId = document.getElementById('upload-pid').value;
    const accNum = document.getElementById('upload-acc').value;

    // Validation: file required
    if (!fileInput.files.length) {
        showAlert("Silakan pilih file DICOM terlebih dahulu", "danger");
        addLog(`[FAILED] Tidak ada file yang dipilih.`, 'error');
        return;
    }

    const fileName = fileInput.files[0].name;

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('patientid', patientId);
    formData.append('accesionnum', accNum);

    showAlert(`Mengunggah dan memodifikasi file: ${fileName}`, "warning");
    addLog(`[UPLOAD] Mengunggah dan memodifikasi: ${fileName}`, 'warning');

    try {
        const resp = await fetch('/api/dicom/upload', {
            method: 'POST',
            body: formData
        });

        let res = {};
        try {
            res = await resp.json();
        } catch {
            res = { message: "Invalid JSON response" };
        }

        if (resp.ok) {
            showAlert(`File ${fileName} berhasil diteruskan ke Router`, "success");
            addLog(`[SUCCESS] File diupload dan berhasil diteruskan ke Router.`, 'info');
            e.target.reset();
        } else {
            showAlert(`Upload gagal: ${res.message}`, "danger");
            addLog(`[FAILED] ${res.message}`, 'error');
        }

    } catch (err) {
        showAlert(`Network Error: ${err}`, "danger");
        addLog(`[ERROR] Gagal upload: ${err}`, 'error');
    }
});

// Download/Save Form
document.getElementById('formSave').addEventListener('submit', async (e) => {
    e.preventDefault();
    const studyUid = document.getElementById('save-study').value;
    addLog(`[SAVE] Menarik file dari PACS untuk download lokal...`, 'warning');
    window.location.href = `/api/dicom/download/${studyUid}`;
});

// Encounter Form
document.getElementById('formEncounter').addEventListener('submit', async (e) => {
    e.preventDefault();

    // Convert datetime-local to ISO8601
    const convertToISO = (datetimeLocal) => {
        if (!datetimeLocal) return null;
        const dt = new Date(datetimeLocal);
        return dt.toISOString();
    };

    const payload = {
        identifier_value: document.getElementById('enc-identifier').value.trim(),
        subject_id: document.getElementById('enc-patient-id').value.trim(),
        subject_display: document.getElementById('enc-patient-name').value.trim(),
        practitioner_id: document.getElementById('enc-practitioner-id').value.trim(),
        practitioner_display: document.getElementById('enc-practitioner-name').value.trim(),
        period_start: convertToISO(document.getElementById('enc-period-start').value),
        period_end: convertToISO(document.getElementById('enc-period-end').value) || undefined,
        location_id: document.getElementById('enc-location-id').value.trim(),
        location_display: document.getElementById('enc-location-name').value.trim()
    };

    // Remove undefined values
    Object.keys(payload).forEach(key => payload[key] === undefined && delete payload[key]);

    showAlert(`Creating Encounter: ${payload.identifier_value}`, "warning");
    addLog(`[ENCOUNTER] Creating encounter with identifier: ${payload.identifier_value}`, 'warning');

    try {
        const resp = await fetch('/api/satset/encounter', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        let res = {};
        try {
            res = await resp.json();
        } catch {
            res = { message: "Invalid JSON response" };
        }

        if (resp.ok) {
            const encounterId = res.encounter_id;
            showAlert(`Encounter created successfully: ${encounterId}`, "success");
            addLog(`[SUCCESS] Encounter created with ID: ${encounterId}`, 'info');
            document.getElementById('encId').innerText = encounterId;
            document.getElementById('encResult').style.display = 'block';
            e.target.reset();
        } else {
            showAlert(`Failed: ${res.message || 'Unknown error'}`, "danger");
            addLog(`[FAILED] ${res.message || 'Server error'}`, 'error');
        }

    } catch (err) {
        showAlert(`Network Error: ${err.message}`, "danger");
        addLog(`[ERROR] Gagal membuat Encounter: ${err.message}`, 'error');
    }
});

// Clear Temporary Files
document.getElementById('btnClearTemp').addEventListener('click', async () => {
    if (!confirm("Hapus semua cache DICOM di server?")) return;
    try {
        const resp = await fetch('/api/dicom/process', { method: 'DELETE' });
        addLog(`[SYSTEM] Folder temporary telah dibersihkan.`);
    } catch (e) {
        addLog(`[SYSTEM] Gagal membersihkan folder.`, 'error');
    }
});

// Clear log console
document.querySelector('.btn-outline-danger').addEventListener('click', () => {
    document.getElementById('logConsole').innerHTML = '';
});

// Service Request Form
document.getElementById('formServiceRequest').addEventListener('submit', async (e) => {
    e.preventDefault();

    // Convert datetime-local to ISO8601
    const convertToISO = (datetimeLocal) => {
        if (!datetimeLocal) return null;
        const dt = new Date(datetimeLocal);
        return dt.toISOString();
    };

    const payload = {
        identifier_value: document.getElementById('sreq-identifier').value.trim(),
        noacsn: document.getElementById('sreq-noacsn').value.trim(),
        subject_id: document.getElementById('sreq-subject-id').value.trim(),
        encounter_id: document.getElementById('sreq-encounter-id').value.trim(),
        period_start: convertToISO(document.getElementById('sreq-period-start').value),
        practitioner_id: document.getElementById('sreq-practitioner-id').value.trim(),
        practitioner_display: document.getElementById('sreq-practitioner-name').value.trim(),
        performer_id: document.getElementById('sreq-performer-id').value.trim(),
        performer_display: document.getElementById('sreq-performer-name').value.trim()
    };

    // Remove undefined values
    Object.keys(payload).forEach(key => payload[key] === undefined && delete payload[key]);

    showAlert(`Creating Service Request: ${payload.identifier_value}`, "warning");
    addLog(`[SERVICE-REQUEST] Creating service request with identifier: ${payload.identifier_value}`, 'warning');

    try {
        const resp = await fetch('/api/satset/service-req', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        let res = {};
        try {
            res = await resp.json();
        } catch {
            res = { message: "Invalid JSON response" };
        }

        if (resp.ok) {
            const serviceRequestId = res.service_request_id;
            showAlert(`Service Request created successfully: ${serviceRequestId}`, "success");
            addLog(`[SUCCESS] Service Request created with ID: ${serviceRequestId}`, 'info');
            document.getElementById('sreqId').innerText = serviceRequestId;
            document.getElementById('sreqResult').style.display = 'block';
            e.target.reset();
        } else {
            showAlert(`Failed: ${res.message || 'Unknown error'}`, "danger");
            addLog(`[FAILED] ${res.message || 'Server error'}`, 'error');
        }

    } catch (err) {
        showAlert(`Network Error: ${err.message}`, "danger");
        addLog(`[ERROR] Gagal membuat Service Request: ${err.message}`, 'error');
    }
});

// Observation Form
document.getElementById('formObservation').addEventListener('submit', async (e) => {
    e.preventDefault();

    // Convert datetime-local to ISO8601
    const convertToISO = (datetimeLocal) => {
        if (!datetimeLocal) return null;
        const dt = new Date(datetimeLocal);
        return dt.toISOString();
    };

    const payload = {
        identifier_value: document.getElementById('obs-identifier').value.trim(),
        codind_code: document.getElementById('obs-coding-code').value.trim(),
        coding_display: document.getElementById('obs-coding-display').value.trim(),
        subject_id: document.getElementById('obs-subject-id').value.trim(),
        subject_display: document.getElementById('obs-subject-display').value.trim(),
        encounter_id: document.getElementById('obs-encounter-id').value.trim(),
        period_start: convertToISO(document.getElementById('obs-period-start').value),
        performer_id: document.getElementById('obs-performer-id').value.trim(),
        performer_display: document.getElementById('obs-performer-display').value.trim(),
        performer_value: document.getElementById('obs-performer-value').value.trim(),
        service_request_id: document.getElementById('obs-service-request-id').value.trim() || undefined,
        imaging_study_id: document.getElementById('obs-imaging-study-id').value.trim() || undefined
    };

    // Remove undefined and empty values
    Object.keys(payload).forEach(key => (!payload[key] || payload[key] === undefined) && delete payload[key]);

    showAlert(`Creating Observation: ${payload.identifier_value}`, "warning");
    addLog(`[OBSERVATION] Creating observation with identifier: ${payload.identifier_value}`, 'warning');

    try {
        const resp = await fetch('/api/satset/observation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        let res = {};
        try {
            res = await resp.json();
        } catch {
            res = { message: "Invalid JSON response" };
        }

        if (resp.ok) {
            const observationId = res.observation_id;
            showAlert(`Observation created successfully: ${observationId}`, "success");
            addLog(`[SUCCESS] Observation created with ID: ${observationId}`, 'info');
            document.getElementById('obsId').innerText = observationId;
            document.getElementById('obsResult').style.display = 'block';
            e.target.reset();
        } else {
            showAlert(`Failed: ${res.message || 'Unknown error'}`, "danger");
            addLog(`[FAILED] ${res.message || 'Server error'}`, 'error');
        }

    } catch (err) {
        showAlert(`Network Error: ${err.message}`, "danger");
        addLog(`[ERROR] Gagal membuat Observation: ${err.message}`, 'error');
    }
});

// Diagnostic Report Form
document.getElementById('formDiagnosticReport').addEventListener('submit', async (e) => {
    e.preventDefault();

    // Convert datetime-local to ISO8601
    const convertToISO = (datetimeLocal) => {
        if (!datetimeLocal) return null;
        const dt = new Date(datetimeLocal);
        return dt.toISOString();
    };

    const payload = {
        identifier_value: document.getElementById('drep-identifier').value.trim(),
        codind_code: document.getElementById('drep-coding-code').value.trim(),
        coding_display: document.getElementById('drep-coding-display').value.trim(),
        subject_id: document.getElementById('drep-subject-id').value.trim(),
        encounter_id: document.getElementById('drep-encounter-id').value.trim(),
        period_start: convertToISO(document.getElementById('drep-period-start').value),
        performer_id: document.getElementById('drep-performer-id').value.trim(),
        imaging_study_id: document.getElementById('drep-imaging-study-id').value.trim() || undefined,
        observation_id: document.getElementById('drep-observation-id').value.trim() || undefined,
        service_request_id: document.getElementById('drep-service-request-id').value.trim() || undefined,
        conclusion_text: document.getElementById('drep-conclusion-text').value.trim() || undefined
    };

    // Remove undefined and empty values
    Object.keys(payload).forEach(key => (!payload[key] || payload[key] === undefined) && delete payload[key]);

    showAlert(`Creating Diagnostic Report: ${payload.identifier_value}`, "warning");
    addLog(`[DIAGNOSTIC-REPORT] Creating diagnostic report with identifier: ${payload.identifier_value}`, 'warning');

    try {
        const resp = await fetch('/api/satset/diag-rep', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        let res = {};
        try {
            res = await resp.json();
        } catch {
            res = { message: "Invalid JSON response" };
        }

        if (resp.ok) {
            const diagnosticReportId = res.diagnostic_report_id;
            showAlert(`Diagnostic Report created successfully: ${diagnosticReportId}`, "success");
            addLog(`[SUCCESS] Diagnostic Report created with ID: ${diagnosticReportId}`, 'info');
            document.getElementById('drepId').innerText = diagnosticReportId;
            document.getElementById('drepResult').style.display = 'block';
            e.target.reset();
        } else {
            showAlert(`Failed: ${res.message || 'Unknown error'}`, "danger");
            addLog(`[FAILED] ${res.message || 'Server error'}`, 'error');
        }

    } catch (err) {
        showAlert(`Network Error: ${err.message}`, "danger");
        addLog(`[ERROR] Gagal membuat Diagnostic Report: ${err.message}`, 'error');
    }
});
