"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.executive import router as executive_router
from app.api.health import router as health_router
from app.config import APP_NAME, CORS_ORIGINS

app = FastAPI(title=APP_NAME)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(health_router, prefix="/api")
app.include_router(executive_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
