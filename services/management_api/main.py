from fastapi import FastAPI

from .database import init_db
from .routers import destinations, sources

app = FastAPI()


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.include_router(sources.router)
app.include_router(destinations.router)
