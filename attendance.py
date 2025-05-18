from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from config import SUPABASE_URL, SUPABASE_KEY
import httpx

router = APIRouter()
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

@router.get("/attendance/{usn}", response_class=HTMLResponse)
async def get_attendance(usn: str):
    async with httpx.AsyncClient() as client:
        # 1. Get student info
        student_res = await client.get(
            f"{SUPABASE_URL}/rest/v1/students?usn=eq.{usn}",
            headers=headers
        )
        student_data = student_res.json()
        if not student_data:
            raise HTTPException(status_code=404, detail="Student not found")
        student = student_data[0]

        # 2. Get attendance logs
        attendance_res = await client.get(
            f"{SUPABASE_URL}/rest/v1/attendance_logs?student_id=eq.{usn}&order=timestamp.desc",
            headers=headers
        )
        logs = attendance_res.json()

    # Calculate attendance stats
    total = len(logs)
    present = sum(1 for log in logs if log["status"] == "present")
    percentage = (present / total) * 100 if total else 0

    # Render HTML
    html = f"""
    <html>
        <head><title>Attendance for {usn}</title></head>
        <body style="font-family:sans-serif;">
            <h2>📘 Attendance Record</h2>
            <p><strong>Name:</strong> {student['name']}</p>
            <p><strong>USN:</strong> {student['usn']}</p>
            <p><strong>Valid Upto:</strong> {student.get('valid_upto', 'N/A')}</p>
            <p><strong>Total Classes:</strong> {total}</p>
            <p><strong>Present:</strong> {present}</p>
            <p><strong>Attendance %:</strong> {percentage:.2f}%</p>

            <h3>🗓 Attendance Log</h3>
            <table border="1" cellpadding="6">
                <tr><th>Date & Time</th><th>Location</th><th>Status</th></tr>
    """

    for log in logs:
        html += f"<tr><td>{log['timestamp']}</td><td>{log['location']}</td><td>{log['status'].capitalize()}</td></tr>"

    html += "</table><br><a href='/admin-dashboard'>⬅ Back to Dashboard</a></body></html>"
    return html
