import configparser
import threading
import queue
import sys
from config.database import MongoDBConnection
from in_progress.filter_in_progress import FilterInProgressDocuments
from process_documents.process_docs import ProcessDocuments
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging


class OCRREngine:
    def __init__(self) -> None:
        try:
            """Initialize Logger and OCRR Engine"""
            logger_config = OCRREngineLogging()
            self.logger = logger_config.configure_logger()
            self.logger.info("| Starting OCRR Engine")

            """Establish OCRR Workspace DB connection"""
            database_name = "ocrrworkspace"
            collection_name = "ocrr"
            db_client = MongoDBConnection().get_connection()
            if db_client is not None:
                self.logger.info("| Connection established with MongoDB")
                """Create OCRRWORKSPACE DB and OCRR collection"""
                db_name_list = db_client.list_database_names()
                if database_name not in db_name_list:
                    self.logger.info(f"| Creating {database_name} database and {collection_name} collection")
                    database = db_client[database_name]
                    database.create_collection(collection_name)
                else:
                    self.logger.info(f"| Reset {collection_name} collection")
                    database = db_client[database_name]
                    collection = database[collection_name]
                    collection.drop()  
            else:
                self.logger.error("| Failed to establish connection to MongoDB.")
                self.logger.info("| Stopping OCRR Engine")
                db_client.close()
                sys.exit(1)

            """Change status 'IN_QUEUE' to 'IN_PROGRESS'"""
            db_upload = db_client["upload"]
            collection_filedetails = db_upload["fileDetails"]
            collection_filedetails.update_many(
                {
                    "status": "IN_QUEUE"
                },
                {
                    "$set": {
                        "status": "IN_PROGRESS"
                    }
                }
            )
            db_client.close()

            """"Set Queue objects"""
            self.in_progress_queue = queue.Queue()
        except Exception as error:
            self.logger.error("| Failed to start OCRR Engine")
            sys.exit(1)

    
    def start_ocrr_engine(self):
        try:
            """
            Thread 1:
                    Query filter upload database fileDetails collection for status:IN_PROGRESS
                    Put the absolute path in Queue
            """
            query_inprogress_obj = FilterInProgressDocuments(upload_path, self.in_progress_queue)
            query_inprogress_thread = threading.Thread(target=query_inprogress_obj.query_in_progress_status)
        
            """Thread 2: Process the documents"""
            process_documents = ProcessDocuments(self.in_progress_queue, upload_path, workspace_path)
            process_document_thread = threading.Thread(target=process_documents.process_docs)

            """Start Thread"""
            query_inprogress_thread.start()
            process_document_thread.start()

            """Wait for threads to finish"""
            query_inprogress_thread.join()
            process_document_thread.join()
        except Exception as error:
            self.logger.error(f"An error occurred during OCRR engine execution: {error}")
            sys.exit(1)

if __name__ == '__main__':
    try:
        """Read config.ini"""
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(r'C:\Program Files (x86)\OCRR\config\config.ini')

        """Get paths"""
        upload_path = config['Paths']['upload']
        workspace_path = config['Paths']['workspace']

        ocrr = OCRREngine()
        ocrr.start_ocrr_engine()
    except Exception as error:
        print(f"Error | {error}")
        sys.exit(1)

