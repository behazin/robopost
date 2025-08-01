import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from prometheus_fastapi_instrumentator import Instrumentator

# Load env variables before other imports
load_dotenv()

from . import api, db

app = FastAPI(title="RoboPost API Gateway")

# Prometheus Metrics
Instrumentator().instrument(app).expose(app)

@app.on_event("startup")
async def startup():
    await db.database.connect()

@app.on_event("shutdown")
async def shutdown():
    await db.database.disconnect()

@app.get("/healthz", tags=["Monitoring"])
async def health_check():
    return {"status": "ok"}

app.include_router(api.router)