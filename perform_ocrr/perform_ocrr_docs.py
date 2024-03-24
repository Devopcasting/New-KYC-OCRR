from config.database import MongoDBConnection
from document_type_identification.identify_documents import DocumentTypeIdentification
from pancard.document_info import PancardDocumentInfo
from aadhaarcard.eaadhaarcard_info import EaadhaarCardInfo
from aadhaarcard.aadhaarcard_info import AaadhaarCardInfo
from passport.document_info import PassportDocumentInfo
from drivingl.document_info import DrivingLicenseDocumentInfo
from cdsl.document_info import CDSLInfo
from e_pancard.document_info import EPancardDocumentInfo
from write_xml_data.xmldata import WriteXMLData
from write_xml_data.rejected_xmldata import RejectedWriteXML
from rejected_doc_redacted.redact_rejected_document import RedactRejectedDocument
from pathlib import Path
import requests
import json
import sys

class PerformOCRROnDocument:
    def __init__(self, document_info: dict) -> None:
        self.document_info = document_info
       
        """Establish MongoDB Connection"""
        try:
            self.db_client = MongoDBConnection().get_connection()
        except Exception as e:
            print(f"Error Connecting Mongodb : {e}")
            sys.exit(1)
    
    def ocrr_docs(self):
        try:
            """Identify Document"""
            document_identification_obj = DocumentTypeIdentification(self.document_info['documentPath'])

            """List of documents methods"""
            processing_document_methods = [
                (document_identification_obj.identify_document("CDSL"), self.process_cdsl),
                (document_identification_obj.identify_document("E-PAN"), self.process_e_pancard),
                (document_identification_obj.identify_document("PAN"), self.process_pancard),
                (document_identification_obj.identify_document("E-Aadhaar"), self.process_e_aadhaarcard),
                (document_identification_obj.identify_document("Aadhaar"), self.process_aadhaarcard),
                (document_identification_obj.identify_document("Bharat Passport"), self.process_passport),
                (document_identification_obj.identify_document("Bharat DL"), self.process_dl)
            ]
        
            identified = False

            for identify_method, process_method in processing_document_methods:
                if identify_method:
                    process_method(self.document_info['documentPath'], self.document_info['redactedPath'],
                                self.document_info['documentName'], self.document_info['taskId'])
                    identified = True
                    break

            """Document is un-identified"""
            if not identified:
                self.unidentified_document_rejected(self.document_info['documentPath'], self.document_info['redactedPath'],
                                                self.document_info['documentName'], self.document_info['taskId'])

            """Remove collection data from ocrr workspace DB"""
            self.remove_collection_data_from_ocrrworkspace(self.document_info['taskId'])

            """Send Post request to webhook"""
            #self.webhook_post_request(self.document_info['taskId'])
        except Exception as e:
            print(f"Error during OCR processing: {e}")
            sys.exit(1)

    """Perform OCRR on Documents"""
    def perform_ocrr_on_docs(self, status, result, document_path, redactedPath, documentName, taskid):

        if status == "REJECTED":
            """Redact 75% and get the coordinates"""
            rejected_doc_coordinates = RedactRejectedDocument(document_path).rejected()
            RejectedWriteXML(redactedPath, documentName, rejected_doc_coordinates).writexml()
            """Update upload db"""
            self.update_upload_filedetails(taskid, "REJECTED", result['message'])
        else:
            """Write Redacted Document XML file"""
            redacted_doc_coordinates = result['data']
            WriteXMLData(redactedPath, documentName, redacted_doc_coordinates ).writexmldata()
            WriteXMLData(redactedPath, documentName, redacted_doc_coordinates ).write_redacted_data_xml()
            """Update upload db"""
            self.update_upload_filedetails(taskid, "REDACTED", result['message'])
        
        """Remove document from workspace"""
        self.remove_document_from_workspace(document_path)

    """Process: Pancard Document"""
    def process_pancard(self, document_path, redactedPath, documentName, taskid):
        result = PancardDocumentInfo(document_path).collect_pancard_info()
        status = result['status']
        self.perform_ocrr_on_docs(status, result, document_path, redactedPath, documentName, taskid)

    """Process: E-Pancard Document"""
    def process_e_pancard(self, document_path, redactedPath, documentName, taskid):
        result = EPancardDocumentInfo(document_path).collect_e_pancard_info()
        status = result['status']
        self.perform_ocrr_on_docs(status, result, document_path, redactedPath, documentName, taskid)

    """Process: E-aadhaarcard Document """
    def process_e_aadhaarcard(self, document_path, redactedPath, documentName, taskid ):
        result = EaadhaarCardInfo(document_path).collect_eaadhaarcard_info()
        status = result['status']
        self.perform_ocrr_on_docs(status, result, document_path, redactedPath, documentName, taskid)
        
    """Process: Aadhaarcard Document"""
    def process_aadhaarcard(self, document_path, redactedPath, documentName, taskid):
        result = AaadhaarCardInfo(document_path).collect_aadhaarcard_info()
        status = result['status']
        self.perform_ocrr_on_docs(status, result, document_path, redactedPath, documentName, taskid)

    """Process: Passport Document"""
    def process_passport(self, document_path, redactedPath, documentName, taskid ):
        result = PassportDocumentInfo(document_path).collect_passport_info()
        status = result['status']
        self.perform_ocrr_on_docs(status, result, document_path, redactedPath, documentName, taskid)
        
    """Process: Driving License Document"""
    def process_dl(self, document_path, redactedPath, documentName, taskid ):
        result = DrivingLicenseDocumentInfo(document_path).collect_dl_info()
        status = result['status']
        self.perform_ocrr_on_docs(status, result, document_path, redactedPath, documentName, taskid)
        
    """Process: CDSL Document"""
    def process_cdsl(self, document_path, redactedPath, documentName, taskid):
        result = CDSLInfo(document_path).collect_cdsl_info()
        status = result['status']
        self.perform_ocrr_on_docs(status, result, document_path, redactedPath, documentName, taskid)

    def remove_collection_data_from_ocrrworkspace(self, taskid):
        database_name = "ocrrworkspace"
        collection_name = "ocrr"
        database = self.db_client[database_name]
        collection = database[collection_name]
        remove_query = {"taskId": taskid}
        collection.delete_one(remove_query)
    
    def update_upload_filedetails(self, taskid, status, message):
        database_name = "upload"
        collection_name = "fileDetails"
        database = self.db_client[database_name]
        collection = database[collection_name]
        filter_query = {"taskId": taskid}
        update = {"$set" : {
            "status": status,
            "taskResult": message
        }}
        collection.update_one(filter_query, update)
    
    def remove_document_from_workspace(self, document_path):
        path = Path(document_path)
        path.unlink()
    
    def unidentified_document_rejected(self, document_path, redactedPath, documentName, taskid):
        """Redact 75% and get the coordinates"""
        rejected_doc_coordinates = RedactRejectedDocument(document_path).rejected()
        RejectedWriteXML(redactedPath, documentName, rejected_doc_coordinates).writexml()
        """Update upload db"""
        self.update_upload_filedetails(taskid, "REJECTED", "Unidentified Document")
        """Remove document from workspace"""
        self.remove_document_from_workspace(document_path)
    
    def webhook_post_request(self, taskid):
        database_name = "upload"

        """get the payload data from filedetails collection"""
        collection_name = "fileDetails"
        database = self.db_client[database_name]
        collection = database[collection_name]
        taskid_to_filter = {"taskId": taskid}
        result = collection.find_one(taskid_to_filter)
        client_id = result['clientId']
        payload = {
            "taskId": result['taskId'],
            "status": result["status"],
            "taskResult": result["taskResult"],
            "clientId": result["clientId"],
            "uploadDir": result["uploadDir"]
        }

        """Get Client Webhook URL from webhook DB"""
        collection_name = "webhooks"
        database = self.db_client[database_name]
        collection = database[collection_name]
        filter_query = {"clientId": client_id}
        client_doc = collection.find_one(filter_query)
        if client_doc:
            WEBHOOK_URL = client_doc["url"]
            HEADER = {'Content-Type': 'application/json'}
            requests.post(WEBHOOK_URL+"/CVCore/processstatus", data=json.dumps(payload), headers=HEADER)
        else:
            print("Error Connecting WebHook")

























