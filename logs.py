from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
import io
import csv
from config import SUPABASE_URL, SUPABASE_KEY

router = APIRouter()

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}


@router.get("/logs/view")
async def view_logs(date: str = "", usn: str = ""):
    try:
        filters = []

        if date:
            filters.append(f"log_date=eq.{date}")

        if usn:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{SUPABASE_URL}/rest/v1/nfc_rings?student_usn=eq.{usn}", headers=headers)
                ring_data = res.json()
                uids = [r["nfc_uid"] for r in ring_data]

            if not uids:
                return JSONResponse(content={"logs": []})

            filters.append("or=(" + ",".join([f"nfc_uid_scanner.eq.{uid}" for uid in uids]) + ")")

        query_string = "&".join(filters)

        async with httpx.AsyncClient() as client:
            hostel_logs = await client.get(f"{SUPABASE_URL}/rest/v1/hostel_access_logs?{query_string}", headers=headers)
            library_logs = await client.get(f"{SUPABASE_URL}/rest/v1/library_access_logs?{query_string}", headers=headers)

        hostel_data = hostel_logs.json()
        library_data = library_logs.json()

        logs = []
        for log in hostel_data:
            logs.append({
                "student_id": log["nfc_uid_scanner"],
                "timestamp": log["entry_time"],
                "location": log["reader_id"],
                "entry_type": "hostel"
            })

        for log in library_data:
            logs.append({
                "student_id": log["nfc_uid_scanner"],
                "timestamp": log["entry_time"],
                "location": log["reader_id"],
                "entry_type": "library"
            })

        return JSONResponse(content={"logs": logs})
    
    except Exception as e:
        return JSONResponse(content={"error": str(e)})


@router.get("/logs/download")
async def download_logs(date: str = "", usn: str = ""):
    # Reuse logic from view_logs to build logs list
    filters = []

    if date:
        filters.append(f"log_date=eq.{date}")

    if usn:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{SUPABASE_URL}/rest/v1/nfc_rings?student_usn=eq.{usn}", headers=headers)
            ring_data = res.json()
            uids = [r["nfc_uid"] for r in ring_data]

        if not uids:
            return StreamingResponse(io.StringIO("No Data Found"), media_type="text/csv")

        filters.append("or=(" + ",".join([f"nfc_uid_scanner.eq.{uid}" for uid in uids]) + ")")

    query_string = "&".join(filters)

    async with httpx.AsyncClient() as client:
        hostel_logs = await client.get(f"{SUPABASE_URL}/rest/v1/hostel_access_logs?{query_string}", headers=headers)
        library_logs = await client.get(f"{SUPABASE_URL}/rest/v1/library_access_logs?{query_string}", headers=headers)

    hostel_data = hostel_logs.json()
    library_data = library_logs.json()

    logs = []
    for log in hostel_data:
        logs.append({
            "student_id": log["nfc_uid_scanner"],
            "timestamp": log["entry_time"],
            "location": log["reader_id"],
            "entry_type": "hostel"
        })

    for log in library_data:
        logs.append({
            "student_id": log["nfc_uid_scanner"],
            "timestamp": log["entry_time"],
            "location": log["reader_id"],
            "entry_type": "library"
        })

    # CSV export
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["student_id", "timestamp", "location", "entry_type"])
    writer.writeheader()
    writer.writerows(logs)
    output.seek(0)

    return StreamingResponse(output, media_type="text/csv", headers={
        "Content-Disposition": f"attachment; filename=logs_{date or usn or 'all'}.csv"
    })
