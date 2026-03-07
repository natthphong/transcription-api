from fastapi import FastAPI
from app.config import load_settings
from app.routes.health import router as health_router
from app.routes.youtube import router as youtube_router
from app.routes.storage import router as storage_router

settings = load_settings()

app = FastAPI(title=settings.app_name)
app.include_router(health_router)
app.include_router(youtube_router)
app.include_router(storage_router)

@app.get("/")
async def root():
    return {"service": settings.app_name, "env": settings.env}
