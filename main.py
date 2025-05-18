from fastapi import FastAPI
from routers import scan, admin, attendance, library
from routers import logs
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with ["http://127.0.0.1:3000"] for more security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(scan.router)
app.include_router(admin.router)
app.include_router(attendance.router)
app.include_router(library.router)
app.include_router(logs.router)
