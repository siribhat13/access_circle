import httpx
from config import SUPABASE_URL, SUPABASE_KEY

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# 1. Get USN from nfc_uid
async def get_usn_by_nfc_uid(nfc_uid: str):
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{SUPABASE_URL}/rest/v1/nfc_rings?nfc_uid=eq.{nfc_uid}",
            headers=headers
        )
        return res.json()

# 2. Get student info from USN
async def get_student_by_usn(usn: str):
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{SUPABASE_URL}/rest/v1/students?usn=eq.{usn}",
            headers=headers
        )
        return res.json()

# ✅ 3. Log access entry to correct log table
async def log_access(data: dict, mode: str = "hostel"):
    table = "hostel_access_logs" if mode == "hostel" else "library_access_logs"

    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers=headers,
            json=data
        )
        print("Status Code:", res.status_code)
        print("Response Text:", res.text)

        try:
            return res.json()
        except Exception:
            return {"error": "Invalid JSON in response", "text": res.text, "status_code": res.status_code}

