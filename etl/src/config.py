import os
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# DIRETÓRIO BASE DO ETL
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# DIRETÓRIOS DOS DADOS
# ============================================================

RAW_DIR = BASE_DIR / "data" / "raw"

EXTRACTED_DIR = BASE_DIR / "data" / "extracted"


# ============================================================
# VARIÁVEIS DE AMBIENTE
# ============================================================

load_dotenv(BASE_DIR / ".env")


# ============================================================
# POSTGRESQL
# ============================================================

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5433")
DB_NAME = os.getenv("POSTGRES_DB", "observatorio")
DB_USER = os.getenv("POSTGRES_USER", "observatorio")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "observatorio_dev")


DATABASE_CONFIG = {
    "host": DB_HOST,
    "port": DB_PORT,
    "database": DB_NAME,
    "user": DB_USER,
    "password": DB_PASSWORD,
}