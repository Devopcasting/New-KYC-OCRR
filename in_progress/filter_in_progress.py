from config.database import MongoDBConnection
from time import sleep
import sys

class FilterInProgressDocuments:
    def __init__(self, upload_path: str, in_progress_queue: object) -> None:
        self.upload_path = upload_path
        self.in_progress_queue = in_progress_queue

        try:
            """Establish connection with upload DB"""
            connection = MongoDBConnection()
            client = connection.get_connection()
            db_upload = client["upload"]
            self.collection_filedetails = db_upload["fileDetails"]

            """Establish connection with ocrrworkspace DB """
            db_ocrrworkspace = client["ocrrworkspace"]
            self.collection_ocrr = db_ocrrworkspace['ocrr']
        except Exception as e:
            print(f"Error establishing MongoDB connection: {e}")
            sys.exit(1)

    
    def query_in_progress_status(self):
        """
            Query database with filter status:IN_PROGRESS
            Put the absolute document path in queue
        """
        try:
            query = {"status": "IN_PROGRESS"}
            while True:
                documents = self.collection_filedetails.find(query)
                document_path = ""
                document_sub_path = ""
                document_path_list = []

                for document in documents:
                    document_path_list = document['uploadDir'].split('/')
                    for i in range(len(document_path_list)):
                        if len(document_path_list[i]) !=0:
                            document_sub_path += '\\'+document_path_list[i]

                    document_path = self.upload_path+document_sub_path
                    status = document['status']
                    clientid = document['clientId']
                    taskid = document['taskId']
                    uploaddir = document['uploadDir']

                    """Insert document info. into ocrrworkspace"""
                    self.insert_inprogress_document_info(taskid, document_path, status, clientid, uploaddir)
                    document_path = ""
                    document_sub_path = ""
                    document_path_list = []
                sleep(5)

        except Exception as e:
            print(f"Error establishing MongoDB connection: {e}")
            sys.exit(1)



    def insert_inprogress_document_info(self, taskid: str, document_path: str, status: str, clientid: str, uploaddir: str):
        """
            Insert new IN_PROGRESS status document info. in ocrrworkspace DB
            Put the absolute document path in queue
        """
        try:
            if self.check_existing_taskid(taskid):
                document_info = {
                    "taskId": taskid,
                    "path": document_path,
                    "status": status,
                    "clientId": clientid,
                    "taskResult": "",
                    "uploadDir": uploaddir
                }
                self.collection_ocrr.insert_one(document_info)
                self.in_progress_queue.put(document_info)
                self.update_inprogress_status(taskid)
        except Exception as e:
            print(f"Error establishing MongoDB connection: {e}")
            sys.exit(1)


    def check_existing_taskid(self, taskid: str) -> bool:
        try:
            query = {"taskId": taskid}
            query_result = self.collection_ocrr.find_one(query)
            if not query_result:
                return True
            return False
        except Exception as e:
            print(f"Error establishing MongoDB connection: {e}")
            sys.exit(1)


    def update_inprogress_status(self, taskid: str):
        try:
            query = {"taskId": taskid}
            update = {"$set":{"status": "IN_QUEUE"}}
            self.collection_filedetails.update_one(query, update)
        except Exception as e:
            print(f"Error updating in-progress status: {e}")
            sys.exit(1)
