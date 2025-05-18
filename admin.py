from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
import httpx
from config import SUPABASE_URL, SUPABASE_KEY

router = APIRouter()

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}


@router.get("/admin-dashboard", response_class=HTMLResponse)
async def admin_dashboard():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SUPABASE_URL}/rest/v1/students", headers=headers)
        students = response.json()

    html = """
    <html>
        <head><title>Admin Dashboard</title></head>
        <body style='font-family:sans-serif'>
            <h2>📋 Admin Dashboard</h2>
            <table border='1' cellpadding='8'>
                <tr><th>Name</th><th>USN</th><th>Scan History</th></tr>
    """
    for s in students:
        html += f"<tr><td>{s['name']}</td><td>{s['usn']}</td><td><a href='/scan-history/{s['usn']}'>View</a></td></tr>"
    html += "</table></body></html>"

    return html


@router.get("/scan-history/{usn}", response_class=HTMLResponse)
async def scan_history(usn: str):
    try:
        async with httpx.AsyncClient() as client:
            # 1. Fetch Main Gate Logs
            main_res = await client.get(
                f"{SUPABASE_URL}/rest/v1/access_logs?student_id=eq.{usn}&order=timestamp.desc",
                headers=headers
            )
            main_logs = main_res.json()

            # 2. Get NFC UIDs
            ring_res = await client.get(
                f"{SUPABASE_URL}/rest/v1/nfc_rings?student_usn=eq.{usn}",
                headers=headers
            )
            rings = ring_res.json()
            nfc_uids = [r["nfc_uid"] for r in rings if isinstance(r, dict) and "nfc_uid" in r]

            # 3. Get hostel and library logs
            hostel_logs, library_logs = [], []
            for uid in nfc_uids:
                h_res = await client.get(
                    f"{SUPABASE_URL}/rest/v1/hostel_access_logs?nfc_uid_scanner=eq.{uid}",
                    headers=headers
                )
                l_res = await client.get(
                    f"{SUPABASE_URL}/rest/v1/library_access_logs?nfc_uid_scanner=eq.{uid}",
                    headers=headers
                )
                hostel_logs += h_res.json()
                library_logs += l_res.json()

        # Render HTML
        html = f"<html><body><h2>📑 Full Scan History for {usn}</h2>"

        # 🏫 Main Gate
        html += "<h3>🏫 Main Gate Logs</h3><table border='1'><tr><th>Timestamp</th><th>Location</th><th>Entry Type</th></tr>"
        for log in main_logs:
            if isinstance(log, dict):
                html += f"<tr><td>{log.get('timestamp')}</td><td>{log.get('location')}</td><td>{log.get('entry_type')}</td></tr>"
        html += "</table><br>"

        # 📚 Library
        html += "<h3>📚 Library Logs</h3><table border='1'><tr><th>Entry</th><th>Exit</th><th>Reader ID</th></tr>"
        for log in library_logs:
            if isinstance(log, dict):
                html += f"<tr><td>{log.get('entry_time')}</td><td>{log.get('exit_time') or '—'}</td><td>{log.get('reader_id')}</td></tr>"
        html += "</table><br>"

        # 🏠 Hostel
        html += "<h3>🏠 Hostel Logs</h3><table border='1'><tr><th>Entry</th><th>Exit</th><th>Reader ID</th></tr>"
        for log in hostel_logs:
            if isinstance(log, dict):
                html += f"<tr><td>{log.get('entry_time')}</td><td>{log.get('exit_time') or '—'}</td><td>{log.get('reader_id')}</td></tr>"
        html += "</table><br>"

        html += "<a href='/admin-dashboard'>⬅ Back to Dashboard</a></body></html>"
        return html

    except Exception as e:
        return HTMLResponse(f"<h1>🔥 Internal Server Error</h1><pre>{str(e)}</pre>", status_code=500)



