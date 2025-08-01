from fastapi import FastAPI
from prometheus_client import make_asgi_app

def setup_monitoring_app() -> FastAPI:
    """Creates a simple FastAPI app to expose Prometheus metrics."""
    monitoring_app = FastAPI(docs_url=None, redoc_url=None) # Disable docs for this internal app
    metrics_app = make_asgi_app()
    monitoring_app.mount("/metrics", metrics_app)

    @monitoring_app.get("/healthz")
    async def health_check():
        return {"status": "ok"}

    return monitoring_app