import os
import sys
import cv2
import shutil
from time import sleep
from perform_ocrr.perform_ocrr_docs import PerformOCRROnDocument
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging

class ProcessDocuments:
    def __init__(self, inprogress_queue: object, upload_path: str, workspace_path: str) -> None:
        """Logger"""
        logger_config = OCRREngineLogging()
        self.logger = logger_config.configure_logger()

        self.inprogress_queue = inprogress_queue
        self.upload_path = upload_path
        self.workspace_path = workspace_path
    
    def process_docs(self):
        while True:
            try:
                document_info = self.inprogress_queue.get()
                if document_info is not None:
                    """Pre-Processing docuement"""
                    self.logger.info(f"| Pre-Processing document {document_info['path']}")
                    document_name_prefix = self.get_prefix_name(document_info['path'])
                    document_name = os.path.basename(document_info['path'])
                    renamed_doc_name = f"{document_name_prefix}{document_name}"
                    jpeg_path = os.path.join(self.workspace_path, renamed_doc_name)

                
                    """Copy document to workspace"""
                    shutil.copy(document_info['path'], jpeg_path)

                    """Check if document is grayscaled"""
                    if not self.check_grayscale_document(jpeg_path):
                        """Perform Pre-Processing"""
                        self.pre_process_docs(jpeg_path, renamed_doc_name)

                    """Perform OCR-Redaction and Prepare XML file"""
                    document_info_dict = {
                            "taskId": document_info['taskId'],
                            "roomName": document_name_prefix.split('+')[0],
                            "roomID": document_name_prefix.split('+')[1],
                            "documentName": document_name,
                            "documentPath": jpeg_path,
                            "uploadPath": self.upload_path,
                            "rejectedPath": self.upload_path+"\\"+document_name_prefix.split('+')[0]+"\\"+document_name_prefix.split('+')[1]+"\\"+"Rejected",
                            "redactedPath": self.upload_path+"\\"+document_name_prefix.split('+')[0]+"\\"+document_name_prefix.split('+')[1]+"\\"+"Redacted"
                        }
                    PerformOCRROnDocument(document_info_dict).ocrr_docs()
                sleep(5)
            except Exception as e:
                self.logger.error(f"Error processing document: {str(e)}")
                sys.exit(1)
                

    
    def pre_process_docs(self, jpeg_path: str, renamed_doc_name: str):
        # Document processing cv2 values
        sigma_x = 1
        sigma_y = 1
        sig_alpha = 1.5
        sig_beta = -0.2
        gamma = 0

        """Pre-process document"""
        document = cv2.imread(jpeg_path)
        denoise_document = cv2.fastNlMeansDenoisingColored(document, None,  10, 10, 7, 21)
        gray_document = cv2.cvtColor(denoise_document, cv2.COLOR_BGR2GRAY)
        gaussian_blur_document = cv2.GaussianBlur(gray_document, (5,5), sigmaX=sigma_x, sigmaY=sigma_y )
        sharpened_image = cv2.addWeighted(gray_document, sig_alpha, gaussian_blur_document, sig_beta, gamma)
        sharpened_image_gray = cv2.cvtColor(sharpened_image, cv2.COLOR_GRAY2BGR)
        cv2.imwrite(os.path.join(jpeg_path, renamed_doc_name), sharpened_image_gray)
    
    def check_grayscale_document(self, jpeg_path):
        document = cv2.imread(jpeg_path)
        if len(document.shape) < 3: return True
        if document.shape[2]  == 1: return True
        b,g,r = document[:,:,0], document[:,:,1], document[:,:,2]
        if (b==g).all() and (b==r).all(): return True
        return False

    def get_prefix_name(self, document_path: str) -> str:
        renamed_doc_list = document_path.split("\\")
        renamed_doc = renamed_doc_list[-3]+"+"+renamed_doc_list[-2]+"+"
        return renamed_doc
