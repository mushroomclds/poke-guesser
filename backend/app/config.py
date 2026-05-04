import os
from dotenv import load_dotenv
from .utils.logger import logger

# Only load .env locally — Azure injects env vars directly

#DONT use, its only for dev on local computer, not container, unless you move .env to container as well
# loadedENV = load_dotenv('../../../.env') 
# if loadedENV:
#     logger.info("Loading environment variables from .env")
# else:
#     logger.info("didnt load env vars from .env")


class Config:
    # ── Environment ───────────────────────────────────────────────────────────
    ENV   = os.getenv("FLASK_ENV", "production")          # 'development' | 'production'
    DEBUG = ENV == "development"

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY     = os.getenv("SECRET_KEY", "dev-secret-key1199S!") #needed for session dict
    ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "http://localhost:80")

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:80").split(",")

    # ── Oracle — shared ───────────────────────────────────────────────────────
    ORACLE_USER     = os.getenv("ORACLE_USER")
    ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD")

    # ── Oracle — local (direct TCP, no wallet) ────────────────────────────────
    # DSN format for local Docker Oracle: host:port/service_name
    ORACLE_DSN_LOCAL = os.getenv("ORACLE_DSN_LOCAL", "pokeapp_oracle:1521/FREEPDB1")

    # ── Oracle — cloud (Autonomous DB via wallet / TNS alias) ─────────────────
    ORACLE_DSN_CLOUD  = os.getenv("ORACLE_DSN_CLOUD")   # TNS alias from tnsnames.ora
    ORACLE_WALLET_DIR = os.getenv("ORACLE_WALLET_DIR", "/opt/oracle/instantclient_23_7/network/admin/")

    # ── Resolved at runtime ───────────────────────────────────────────────────
    @classmethod
    def get_oracle_dsn(cls) -> str:
        return cls.ORACLE_DSN_LOCAL if cls.ENV == "development" else cls.ORACLE_DSN_CLOUD

    @classmethod
    def use_wallet(cls) -> bool:
        return cls.ENV != "development"

    # ── APIs ──────────────────────────────────────────────────────────────────
    POKEMON_API_KEY = os.getenv("POKEMON_API_KEY")
    TESTING         = False