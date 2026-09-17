"""Application configuration loaded from environment variables."""

from os import getenv

from dotenv import load_dotenv

load_dotenv()

APP_NAME = getenv("APP_NAME", "Executive Productivity Agent")
CORS_ORIGINS = [
	origin.strip()
	for origin in getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
	if origin.strip()
]
