import os

from dotenv import load_dotenv


load_dotenv()


DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5433")),
    "database": os.getenv("DB_NAME", "observatorio"),
    "user": os.getenv("DB_USER", "observatorio"),
    "password": os.getenv("DB_PASSWORD", "observatorio_dev"),
}


RAW_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        "raw"
    )
)


EXTRACTED_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        "extracted"
    )
)