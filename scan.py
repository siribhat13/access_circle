# scan.py (Final unified version for both viewing and logging scans)
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from supabase_client import get_student_by_usn, get_usn_by_nfc_uid, log_access
from datetime import datetime
import joblib
import numpy as np

router = APIRouter()

# Load models and tools
# Attendance model
attendance_model = joblib.load("ml_models/attendance_model/anomaly_model.pkl")
attendance_scaler = joblib.load("ml_models/attendance_model/scaler.pkl")

# Tracking model
tracking_model = joblib.load("ml_models/tracking_model/anomaly_model.pkl")
tracking_scaler = joblib.load("ml_models/tracking_model/scaler.pkl")
le_location = joblib.load("ml_models/tracking_model/label_encoder_location.pkl")
le_role = joblib.load("ml_models/tracking_model/label_encoder_role.pkl")

@router.get("/nfc-scan/{nfc_uid}", response_class=HTMLResponse)
async def scan_nfc(nfc_uid: str, location: str = "main_gate", mode: str = "hostel"):
    try:
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()

        # Get student USN using NFC UID
        ring_data = await get_usn_by_nfc_uid(nfc_uid)
        if not ring_data:
            return HTMLResponse(content="<h1>❌ Ring not registered</h1>", status_code=404)

        student_usn = ring_data[0]["student_usn"]

        # Get student details using USN
        student_data = await get_student_by_usn(student_usn)
        if not student_data:
            return HTMLResponse(content="<h1>❌ Student not found</h1>", status_code=404)

        student = student_data[0]

        # === ML Prediction Section ===
        anomaly = False  # Default fallback

        if mode == "attendance":
            # Use attendance model (numerical only)
            features = np.array([[hour, weekday]])
            scaled = attendance_scaler.transform(features)
            prediction = attendance_model.predict(scaled)[0]
            anomaly = prediction == -1

        else:
            # Use tracking model (location + role)
            try:
                location_encoded = le_location.transform([location])[0]
                role_encoded = le_role.transform(["student"])[0]  # Assume role = student
                features = np.array([[hour, weekday, location_encoded, role_encoded]])
                scaled = tracking_scaler.transform(features)
                prediction = tracking_model.predict(scaled)[0]
                anomaly = prediction == -1
            except Exception as e:
                print("Encoding error:", str(e))
                anomaly = False

        # Log access
        log_entry = {
            "nfc_uid_scanner": nfc_uid,
            "entry_time": datetime.now().isoformat(),
            "reader_id": location,
            "log_date": datetime.now().date().isoformat(),
            "anomaly": anomaly
        }

        await log_access(log_entry, mode=mode)

        # === Display Result ===
        html = f"""
        <html>
        <head><title>Scan Result</title></head>
        <body style='font-family:sans-serif;'>
            <h2 style='color:{'red' if anomaly else 'green'};'>{'🚨 Anomaly Detected' if anomaly else '✅ Normal Scan'}</h2>
            <p><strong>Name:</strong> {student['name']}</p>
            <p><strong>USN:</strong> {student['usn']}</p>
            <p><strong>Valid Upto:</strong> {student['valid_upto']}</p>
            <img src='{student['image_url']}' alt='Student Image' style='width:200px; border-radius:8px; border:1px solid #aaa;'>
        </body>
        </html>
        """
        return HTMLResponse(content=html)

    except Exception as e:
        return HTMLResponse(content=f"<h1>❌ Error</h1><p>{str(e)}</p>", status_code=500)
