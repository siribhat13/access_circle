from fastapi import APIRouter
from config import SUPABASE_URL, SUPABASE_KEY
import httpx
from datetime import datetime

router = APIRouter()
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

@router.post("/library")
async def update_library(usn: str, book_title: str, action: str):
    entry = {
        "student_id": usn,
        "timestamp": datetime.now().isoformat(),
        "book_title": book_title,
        "action": action  # "issued" or "returned"
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{SUPABASE_URL}/rest/v1/library_logs", json=entry, headers=headers)
        return res.json()

@router.get("/library/{usn}")
async def get_library_logs(usn: str):
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{SUPABASE_URL}/rest/v1/library_logs?student_id=eq.{usn}&order=timestamp.desc",
            headers=headers
        )
        return res.json()
