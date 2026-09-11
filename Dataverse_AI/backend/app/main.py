from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import assistant, dashboard

app = FastAPI(title="UrbanFlow Decision Intelligence API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assistant.router)
app.include_router(dashboard.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
