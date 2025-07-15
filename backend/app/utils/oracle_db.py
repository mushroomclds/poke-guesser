import oracledb
from app.config import Config
from .logger import logger
import sys
import os


class OracleDB:
    """Class for managing Oracle Database connections."""

    def __init__(self):
        """Initialize database connection settings from environment variables."""
        try: 
            # Load environment variables from .env file
            # load_dotenv()
            self.user = Config.ORACLE_USER 
            self.password = Config.ORACLE_PASSWORD
            self.dsn = Config.ORACLE_DSN  # Must match an entry in tnsnames.ora
            self.tns_admin = "/opt/oracle/wallet"
            os.environ['TNS_ADMIN'] = self.tns_admin
            # self.tns_admin = os.getenv('TNS_ADMIN') # Set TNS_ADMIN for Oracle Wallet (if required)
            logger.info(f"Loaded DATABASE_USER: {self.user} \n Loaded DATABASE_DSN: {self.dsn} \
                \n Loaded TNS_ADMIN: {self.tns_admin}" )
            oracledb.init_oracle_client(lib_dir="/opt/oracle/instantclient_23_7")
        except Exception as e: 
            logger.error(f"Error initializing Oracle client: {e}")

    def get_connection(self):
        """Returns a new Oracle database connection."""
        try:
            return oracledb.connect(user=self.user, password=self.password, dsn=self.dsn)
        except Exception as e:
            logger.error(f"Error connecting to Oracle DB: {e}")
            raise

    def test_connection(self):
        """Tests the Oracle database connection."""
        logger.info("Testing Oracle DB connection...")
        conn = self.get_connection()
        if conn:
            logger.info("Oracle DB connection successful.")
            conn.close()
        else:
            logger.error("Oracle DB connection failed.")

    def execute_query(self, query, params=None, fetch_all=True):
        """Executes a SQL query and returns the result."""
        conn = self.get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute(query, params or {})
            conn.commit()  # Commit the transaction after executing the query
            
            logger.info(f"Executed query: {query}")
            
            if fetch_all:
                result = cursor.fetchall()
            else:
                result = cursor.fetchone()
            logger.info(f"Query result: {result}")
            return result
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

db = OracleDB()


if __name__ == "__main__":
    import app.config
    db = OracleDB()
    db.test_connection()
    
