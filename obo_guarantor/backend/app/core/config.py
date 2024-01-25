import os

PROJECT_NAME = "obo_guarantor"

SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
REDIS_URI = os.getenv("REDIS_URL")

API_V1_STR = "/api/v1"
