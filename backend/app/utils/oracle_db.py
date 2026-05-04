import oracledb
from app.config import Config
from .logger import logger
import sys
import os


class OracleDB:
    """Class for managing Oracle Database connections."""

    def __init__(self):
        self.user     = Config.ORACLE_USER
        self.password = Config.ORACLE_PASSWORD
        self.dsn      = Config.get_oracle_dsn()

        if Config.use_wallet():
            os.environ['TNS_ADMIN'] = Config.ORACLE_WALLET_DIR
            oracledb.init_oracle_client(lib_dir="/opt/oracle/instantclient_23_7")
            logger.info(f"Oracle thick mode | DSN={self.dsn} | wallet={Config.ORACLE_WALLET_DIR}")
        else:
            # Thin mode — pure Python, no Instant Client needed locally
            logger.info(f"Oracle thin mode | DSN={self.dsn}")

    def get_connection(self):
        """Returns a new Oracle database connection."""
        try:
            return oracledb.connect(user=self.user, password=self.password, dsn=self.dsn)
        except Exception as e:
            logger.error(f"Error connecting to Oracle DB: {e}")
            raise Exception("At get_connection: Could not get database connection")

    def test_connection(self):
        """Tests the Oracle database connection."""
        logger.info("Testing Oracle DB connection...")
        conn = self.get_connection()
        if conn:
            logger.info("Oracle DB connection successful.")
            conn.close()
        else:
            logger.error("Oracle DB connection failed.")

    def execute_query(self, query, params=None, operation="GET"):
        """Executes a SQL query based on operation type (GET, POST, PUT)."""
        conn = self.get_connection()
        if not conn:
            raise Exception("Could not get database connection")

        try:
            cursor = conn.cursor()
            cursor.execute(query, params or {})
            logger.info(f"Executed query: {query}")

            if operation == "GET":
                result = cursor.fetchall()
                logger.info(f"Query result: {result}")
                return result
            elif operation == "POST":
                conn.commit()
                # result = {
                #     "last_id": cursor.lastrowid,
                #     "rows_affected": cursor.rowcount
                # }
                logger.info(f"Insert result:")
            elif operation == "PUT":
                conn.commit()
                result = {"rows_affected": cursor.rowcount}
                logger.info(f"Rows updated: {result}")
                return result
            else:
                raise ValueError(f"Invalid operation type, operation: {operation}")
        except Exception as e:
            logger.error(f"Database query error with operation {operation}: {e}")
            conn.rollback()
            raise Exception("Database operation failed")
        finally:
            cursor.close()
            conn.close()

db = OracleDB()


if __name__ == "__main__":
    import app.config
    db = OracleDB()
    db.test_connection()
    
