import re
import pytesseract
import datetime
import cv2
import configparser
from PIL import Image
from qreader import QReader
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging
from helper.pancard_text_coordinates import TextCoordinates
from helper.e_pancard_signature_text_coords import EPancardSignatureTextCoordinates

class EPancardDocumentInfo:
    def __init__(self, document_path: str) -> None:

        self.document_path = document_path

        """Read config.ini"""
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(r'C:\Program Files (x86)\OCRR\config\config.ini')
        self.DOCUMENT_MODE = int(config['Mode']['ShowAvailableRedaction'])

        """Logger"""
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()

        """Get the coordinates of all the extracted text"""
        self.coordinates = TextCoordinates(document_path).generate_text_coordinates()

        """Get the coordinates for signature"""
        self.signature_coords = EPancardSignatureTextCoordinates(document_path).generate_text_coordinates()

        """Get the text from document"""
        tesseract_config = r'--oem 3 --psm 11'
        self.text_data = pytesseract.image_to_string(document_path, lang="eng", config=tesseract_config)

        """Get the text for signature identification"""
        self.signature_text_data = pytesseract.image_to_string(document_path)

        """Create a QReader instance"""
        self.qreader = QReader()
    
    """func: extract PAN Card number"""
    def extract_pancard_number(self) -> dict:
        try:
            result = {
                "E-Pancard Number": "",
                "coordinates": []
            }
            pancard_text = ""
            pancard_coordinates = []
        
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if len(text) == 10 and text.isupper() and text.isalnum() and any(char.isdigit() for char in text):
                    pancard_coordinates.append([x1, y1, x2, y2])
                    pancard_text = text
        
            if not pancard_coordinates:
                return result
        
            width = pancard_coordinates[0][2] - pancard_coordinates[0][0]
            result = {
                "E-Pancard Number": pancard_text,
                "coordinates": [[pancard_coordinates[0][0], pancard_coordinates[0][1], 
                       pancard_coordinates[0][0] + int(0.65 * width),pancard_coordinates[0][3]]]
            }
            return result
        except Exception as error:
            result = {
                "E-Pancard Number": "",
                "coordinates": []
            }
            return result

    
    """func: extract dob"""
    def extract_dob(self):
        try:
            result = {
                "E-Pancard DOB": "",
                "coordinates": []
            }
            dob_text = ""
            dob_coordinates = []

            """Data patterns: DD/MM/YYY, DD-MM-YYY"""
            date_pattern = r'\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}'

            for i, (x1, y1, x2, y2, text) in enumerate(self.coordinates):
                match = re.search(date_pattern, text)
                if match:
                    dob_coordinates = [x1, y1, x2, y2]
                    dob_text = text
                    break
            if not dob_coordinates:
                return result
        
            """Get first 6 chars"""
            width = dob_coordinates[2] - dob_coordinates[0]
            result = {
                "E-Pancard DOB": dob_text,
                "coordinates": [[dob_coordinates[0], dob_coordinates[1], dob_coordinates[0] + int(0.54 * width), dob_coordinates[3]]]
            }
            return result
        except Exception as error:
            result = {
                "E-Pancard DOB": "",
                "coordinates": []
            }
            return result

        
    """func: extract gender"""
    def extract_gender(self):
        try:
            result = {
                "E-Pancard Gender": "",
                "coordinates": []
            }
            gender_text = ""
            gender_coordinates = []

            gender_pattern = r"male|female"
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if re.search(gender_pattern, text, flags=re.IGNORECASE):
                    gender_coordinates.append([x1, y1, x2, y2])
                    gender_text = text
                    break
            if not gender_coordinates:
                return result
            
            result = {
                "E-Pancard Gender": gender_text,
                "coordinates": gender_coordinates
            }
            return result
        except Exception as error:
            result = {
                "E-Pancard Gender": "",
                "coordinates": []
            }
            return result

    
    """func: extract name"""
    def extract_name(self):
        try:
            result = {
                "E-Pancard Name": "",
                "coordinates": []
            }
            name_text = ""
            name_coordinates = []
            matching_name_list = []

            clean_text = [i for i in self.text_data.split("\n") if len(i) != 0]
            for i,text in enumerate(clean_text):
                if 'ata /Name' in text:
                    matching_name_list = clean_text[i + 1].split()
                    name_text = clean_text[i + 1]
                    break
        
            if not matching_name_list:
                return result
        
            if len(matching_name_list) > 1:
                matching_name_list = matching_name_list[:-1]

            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if text in matching_name_list:
                    name_coordinates.append([x1, y1, x2, y2])
                if len(matching_name_list) == len(name_coordinates):
                    break
        
            if len(name_coordinates) > 1:
                result = {
                    "E-Pancard Name": name_text,
                    "coordinates": [[name_coordinates[0][0], name_coordinates[0][1], name_coordinates[-1][2], name_coordinates[-1][3]]]
                }
            else:
                result = {
                    "E-Pancard Name": name_text,
                    "coordinates": [[name_coordinates[0][0], name_coordinates[0][1], name_coordinates[0][2], name_coordinates[0][3]]]
                }
            return result
        except Exception as error:
            result = {
                "E-Pancard Name": "",
                "coordinates": []
            }
            return result

    """func: extract father name"""
    def extract_father_name(self):
        try:
            result = {
                "E-Pancard Father's Name": "",
                "coordinates": []
            }
            father_name_text = ""
            father_name_coordinates = []
            matching_name_list = []

            clean_text = [i for i in self.text_data.split("\n") if len(i) != 0]
            for i,text in enumerate(clean_text):
                if 'Father' in text:
                    matching_name_list = clean_text[i + 1].split()
                    father_name_text = clean_text[i + 1]
                    break
        
            if not matching_name_list:
                return result
        
            if len(matching_name_list) > 1:
                matching_name_list = matching_name_list[:-1]

            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if text in matching_name_list:
                    father_name_coordinates.append([x1, y1, x2, y2])
                if len(matching_name_list) == len(father_name_coordinates):
                    break
        
            if len(father_name_coordinates) > 1:
                result = {
                    "E-Pancard Father's Name": father_name_text,
                    "coordinates": [[father_name_coordinates[0][0], father_name_coordinates[0][1], father_name_coordinates[-1][2], father_name_coordinates[-1][3]]]
                }
            else:
                result = {
                    "E-Pancard Father's Name": father_name_text,
                    "coordinates": [[father_name_coordinates[0][0], father_name_coordinates[0][1], father_name_coordinates[0][2], father_name_coordinates[0][3]]]
                }
            return result
        except Exception as error:
            result = {
                "E-Pancard Father's Name": "",
                "coordinates": []
            }
            return result

    """func: redact bottom pancard"""
    def redact_bottom_pancard(self):
        result = {}
        bottom_coordinates = []
        image = Image.open(self.document_path)
        image_width, image_height = image.size
        bottom_coordinates.append(self.bottom_40_percent_coordinates(image_width, image_height))

        result = {
            "E-Pancard": "E-Pancard",
            "coordinates": bottom_coordinates
        }
        return result
    
    def bottom_40_percent_coordinates(self, image_width, image_height) -> list:
        x1 = 0
        y1 = int(0.8 * image_height)  # 60% from the top is 40% from the bottom
        x2 = image_width // 2
        y2 = image_height
        return [x1, y1, x2, y2]

    """func: extract QR code"""
    def extract_qr_code(self):
        result = {}
        qrcode_coordinates = []

        # Load the image
        image = cv2.imread(self.document_path)

        # Detect and decode QR codes
        found_qrs = self.qreader.detect(image)

        if not found_qrs:
            result = {
                "Pancard QR Code": "",
                "coordinates": []
            }
            return result
        """get 50% of QR Code"""
        for i in found_qrs:
            x1, y1, x2, y2 = i['bbox_xyxy']
            qrcode_coordinates.append([int(round(x1)), int(round(y1)), int(round(x2)), (int(round(y1)) + int(round(y2))) // 2])
            #qrcode_coordinates.append([int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))])
        
        result = {
            "QR-Code": f"Found {len(qrcode_coordinates)} QR Codes",
            "coordinates": qrcode_coordinates
        }
        return result
    


    """func: collect e-pancard information"""
    def collect_e_pancard_info(self) -> dict:
        e_pancard_doc_info_list = []

        """Check Document mode"""
        if self.DOCUMENT_MODE == 1:

            """Collect: E-Pancard Number"""
            pancard_number = self.extract_pancard_number()
            if len(pancard_number['coordinates']) != 0:
                e_pancard_doc_info_list.append(pancard_number)
            else:
                e_pancard_doc_info_list.append(pancard_number)
                self.logger.error("| E-Pancard Number not found")
            
            """Collect: E-Pancard DOB"""
            pancard_dob = self.extract_dob()
            if len(pancard_dob['coordinates']) != 0:
                e_pancard_doc_info_list.append(pancard_dob)
            else:
                e_pancard_doc_info_list.append(pancard_dob)
                self.logger.error("| E-Pancard DOB not found")

            """"Collect: E-Pancard Gender"""
            pancard_gender = self.extract_gender()
            if len(pancard_gender['coordinates']) != 0:
                e_pancard_doc_info_list.append(pancard_gender)
            else:
                e_pancard_doc_info_list.append(pancard_gender)
                self.logger.error("| E-Pancard Gender not found")

            """Collect: E-pancard Name"""
            pancard_name = self.extract_name()
            if len(pancard_name['coordinates']) != 0:
                e_pancard_doc_info_list.append(pancard_name)
            else:
                e_pancard_doc_info_list.append(pancard_name)
                self.logger.error("| E-Pancard Name not found")

            """Collect: E-pancard Father's name"""
            pancard_father_name = self.extract_father_name()
            if len(pancard_father_name['coordinates']) != 0:
                e_pancard_doc_info_list.append(pancard_father_name)
            else:
                e_pancard_doc_info_list.append(pancard_father_name)
                self.logger.error("| E-Pancard Father's Name not found")

            """Collect: QR-Code"""
            qr_code = self.extract_qr_code()
            if len(qr_code['coordinates']) != 0:
                e_pancard_doc_info_list.append(qr_code)
            else:
                e_pancard_doc_info_list.append(qr_code)
                self.logger.error("| E-Pancard QR Code not found")

            """Collect: Bottom Pancard"""
            bottom_pancard = self.redact_bottom_pancard()
            e_pancard_doc_info_list.append(bottom_pancard)
            
            """check pancard_doc_info_list"""
            all_keys_and_coordinates_empty =  all(all(not v for v in d.values()) for d in e_pancard_doc_info_list)
            if all_keys_and_coordinates_empty:
                return {"message": "Unable to extract E-Pancard information", "status": "REJECTED"}
            else:
                return {"message": "Successfully Redacted E-PAN Card Document", "status": "REDACTED", "data": e_pancard_doc_info_list}
        else:
            """Collect: E-Pancard Number"""
            pancard_number = self.extract_pancard_number()
            if len(pancard_number['coordinates']) != 0:
                e_pancard_doc_info_list.append(pancard_number)
            else:
                return {"message": "Unable to extract E-Pancard Number not found", "status": "REJECTED"}
            
            """Collect: E-Pancard DOB"""
            pancard_dob = self.extract_dob()
            if len(pancard_dob['coordinates']) != 0:
                e_pancard_doc_info_list.append(pancard_dob)
            else:
                return {"message": "Unable to extract E-Pancard DOB", "status": "REJECTED"}

            """"Collect: E-Pancard Gender"""
            pancard_gender = self.extract_gender()
            if len(pancard_gender['coordinates']) != 0:
                e_pancard_doc_info_list.append(pancard_gender)
            else:
                return {"message": "Unable to extract E-Pancard Gender", "status": "REJECTED"}

            """Collect: E-pancard Name"""
            pancard_name = self.extract_name()
            if len(pancard_name['coordinates']) != 0:
                e_pancard_doc_info_list.append(pancard_name)
            else:
                return {"message": "Unable to extract E-Pancard User name", "status": "REJECTED"}

            """Collect: E-pancard Father's name"""
            pancard_father_name = self.extract_father_name()
            if len(pancard_father_name['coordinates']) != 0:
                e_pancard_doc_info_list.append(pancard_father_name)
            else:
                return {"message": "Unable to extract E-Pancard Father's name", "status": "REJECTED"}

            """Collect: QR-Code"""
            qr_code = self.extract_qr_code()
            if len(qr_code['coordinates']) != 0:
                e_pancard_doc_info_list.append(qr_code)
            else:
                return {"message": "Unable to extract E-Pancard QR-Code", "status": "REJECTED"}

            """Collect: Bottom Pancard"""
            bottom_pancard = self.redact_bottom_pancard()
            e_pancard_doc_info_list.append(bottom_pancard)
            
          
            return {"message": "Successfully Redacted E-PAN Card Document", "status": "REDACTED", "data": e_pancard_doc_info_list}


