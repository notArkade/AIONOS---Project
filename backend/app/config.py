"""Application configuration loaded from environment variables."""

from os import getenv

from dotenv import load_dotenv

load_dotenv()

APP_NAME = getenv("APP_NAME", "Executive Productivity Agent")
