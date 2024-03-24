import pymongo
import subprocess
from time import sleep
from pymongo.errors import ConnectionFailure
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging

class MongoDBConnection:
    def __init__(self) -> None:
        self.connection = "mongodb://localhost:27017"
        """Logger"""
        logger_config = OCRREngineLogging()
        self.logger = logger_config.configure_logger()
    
    def get_connection(self):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                client = pymongo.MongoClient(self.connection)
                client.admin.command('ping')
                return client
            except ConnectionFailure as e:
                self.logger.info(f"Connection attempt {attempt+1} failed: {e}")
                """Try to start the MongoDB service"""
                subprocess.run(["net", "start", "MongoDB"])
                if attempt < max_retries - 1:
                    sleep(5)
                else:
                    raise ConnectionError("Failed to establish a connection to MongoDB.")        