import os
from datetime import timedelta
from urllib.parse import urlparse, unquote

from dotenv import load_dotenv

load_dotenv()


def _parse_mysql_url(url):
    """Parse MySQL URL to mysql-connector config."""
    parsed = urlparse(url)
    if parsed.scheme not in {"mysql", "mysql+pymysql", "mariadb"}:
        return {}

    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or "root"),
        "password": unquote(parsed.password or ""),
        "database": (parsed.path or "/ug_feedback_db").lstrip("/") or "ug_feedback_db",
    }


# Railway and cloud providers often expose DATABASE_URL/MYSQL_URL.
_url_config = _parse_mysql_url(
    os.getenv("DATABASE_URL")
    or os.getenv("MYSQL_URL")
    or os.getenv("MYSQL_PUBLIC_URL")
    or ""
)

DB_CONFIG = {
    "host": os.getenv("DB_HOST") or os.getenv("MYSQLHOST") or _url_config.get("host", "localhost"),
    "port": int(os.getenv("DB_PORT") or os.getenv("MYSQLPORT") or _url_config.get("port", 3306)),
    "user": os.getenv("DB_USER") or os.getenv("MYSQLUSER") or _url_config.get("user", "root"),
    "password": os.getenv("DB_PASSWORD") or os.getenv("MYSQLPASSWORD") or _url_config.get("password", ""),
    "database": os.getenv("DB_NAME") or os.getenv("MYSQLDATABASE") or _url_config.get("database", "ug_feedback_db"),
}

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))

# Session configuration
SESSION_LIFETIME = timedelta(hours=2)
PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

# Password requirements
MIN_PASSWORD_LENGTH = 6
BCRYPT_ROUNDS = 12

# Academic year settings
CURRENT_ACADEMIC_YEAR = os.getenv("ACADEMIC_YEAR", "2025-26")
CURRENT_SEMESTER = int(os.getenv("SEMESTER", "2"))
