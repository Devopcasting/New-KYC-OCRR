import re
import pytesseract
import datetime
import cv2
import configparser
from qreader import QReader
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging
from helper.pancard_text_coordinates import TextCoordinates
from helper.pancard_signature_text_coordinates import SignatureTextCoordinates
from pancard.pattern2 import PanCardPattern2
from pancard.pattern1 import PanCardPattern1

class PancardDocumentInfo:
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
        self.signature_coords = SignatureTextCoordinates(document_path).generate_text_coordinates()

        """Get the text from document"""
        tesseract_config = r'--oem 3 --psm 11'
        self.text_data = pytesseract.image_to_string(document_path, lang="eng", config=tesseract_config)

        """Get the text for signature identification"""
        self.signature_text_data = pytesseract.image_to_string(document_path)

        """Create a QReader instance"""
        self.qreader = QReader()
    
    """func: extract pancard number"""
    def extract_pancard_number(self) -> dict:
        try:
            result = {
                    "Pancard Number": "",
                    "coordinates": []
                }
            pancard_text = ""
            pancard_coordinates = []
            matching_text_index = None
            matching_text_regex = r"\b(?:permanent|pe@fanent|pe@ffignent|pertianent|account|number|card|perenent|accoun|pormanent|petraancnt)\b"

            """find matching text pattern"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if re.search(matching_text_regex, text.lower(), flags=re.IGNORECASE):
                    matching_text_index = i
                    break

            if matching_text_index is None:
                """find pancard number without matching pattern text"""
                for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                    if len(text) == 10 and text.isupper() and text.isalnum():
                        pancard_coordinates = [x1, y1, x2, y2]
                        pancard_text = text
                        break
                    elif len(text) == 10 and text.isalnum():
                        pancard_coordinates = [x1, y1, x2, y2]
                        pancard_text = text.capitalize()
                        break          
            else:
                """find pancard using matching pattern text index"""
                for i in range(matching_text_index,  len(self.coordinates)):
                    text = self.coordinates[i][4]
                    if len(text) == 10 and text.isupper() and text.isalnum():
                        pancard_coordinates = [self.coordinates[i][0], self.coordinates[i][1], self.coordinates[i][2], self.coordinates[i][3]]
                        pancard_text = text
                        break
                    elif len(text) == 10 and text.isalnum():
                        pancard_coordinates = [self.coordinates[i][0], self.coordinates[i][1], self.coordinates[i][2], self.coordinates[i][3]]
                        pancard_text = text.capitalize()
                        break

            if not pancard_coordinates:
                return result
        
            width = pancard_coordinates[2] - pancard_coordinates[0]
            result = {
                "Pancard Number": pancard_text,
                "coordinates": [[pancard_coordinates[0], pancard_coordinates[1], 
                       pancard_coordinates[0] + int(0.65 * width),pancard_coordinates[3]]]
            }
            return result
        except Exception as error:
            result = {
                    "Pancard Number": "",
                    "coordinates": []
                }
            return result

    """func: extract dob"""
    def extract_dob(self):
        try:
            result = {
                "Pancard DOB": "",
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
                "Pancard DOB": dob_text,
                "coordinates": [[dob_coordinates[0], dob_coordinates[1], dob_coordinates[0] + int(0.54 * width), dob_coordinates[3]]]
            }
            return result
        except Exception as error:
            result = {
                "Pancard DOB": "",
                "coordinates": []
            }
            return result

        

    """func: extract signature"""
    def extract_signature(self, pattern_no):
        try:
            result = {
                "Pancard Signature": "",
                "coordinates": []
                }
            matching_text_keyword = ["signature", "nature"]
            signature_coordinates = []

            if pattern_no == 1:
                """get the coordinates"""
                for i,(x1, y1, x2, y2, text) in enumerate(self.signature_coords):
                    if text.lower() in matching_text_keyword:
                        signature_coordinates.append([self.signature_coords[i + 1][0], self.signature_coords[i + 1][1],
                                                   self.signature_coords[i + 1][2], self.signature_coords[i + 1][3] ])
                        # signature_coordinates.append([self.signature_coords[i + 2][0], self.signature_coords[i + 2][1], 
                        #                               self.signature_coords[i + 2][2], self.signature_coords[i + 2][3] ])
            
                if not signature_coordinates:
                    return result
            
                result = {
                    "Pancard Signature": "User Signature",
                    "coordinates": signature_coordinates
                }
                return result

            else:

                """get the coordinates"""
                for i,(x1, y1, x2, y2, text) in enumerate(self.signature_coords):
                    if text.lower() in matching_text_keyword:
                        signature_coordinates.append([self.signature_coords[i - 1][0], self.signature_coords[i - 1][1], 
                                                  self.signature_coords[i - 1][2], self.signature_coords[i - 1][3] ])
                        break
            
                if not signature_coordinates:
                    return result
            
                result = {
                    "Pancard Signature": "User Signature",
                    "coordinates": signature_coordinates
                }
                return result
        except Exception as error:
            result = {
                    "Pancard Signature": "",
                    "coordinates": []
                    }
            return result


    """func: extract QR code"""
    def extract_qr_code(self):
        try:
            result = {
                "Pancard QR Code": "",
                "coordinates": []
            }
            qrcode_coordinates = []

            # Load the image
            image = cv2.imread(self.document_path)

            # Detect and decode QR codes
            found_qrs = self.qreader.detect(image)

            if not found_qrs:
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
        except Exception as error:
            result = {
                "Pancard QR Code": "",
                "coordinates": []
            }
            return result

    """func: find matching text position"""
    def __find_matching_text(self, lines, matching_text_keyword):
        for i,line in enumerate(lines):
            for k in matching_text_keyword:
                if k.lower() in line.lower():
                    return i
        return 404
    

    """func: identify pancard pattern"""
    def identify_pancard_pattern(self) -> int:
        pancard_pattern_keyword_search = ["name", "father's", "father", "/eather's", "uiname"]
        for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
            if text.lower() in pancard_pattern_keyword_search:
                return 1
        return 2

    """func: validate date"""
    def validate_date(self, date_str: str, split_pattern: str) -> bool:
        try:
            # Split the date string into day, month, and year
            day, month, year = map(int, date_str.split(split_pattern))
            # Check if the date is within valid ranges
            if not (1 <= day <= 31 and 1 <= month <= 12 and 1000 <= year <= 9999):
                return False
            # Check for leap year if necessary
            if month == 2 and day > 28 and not (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
                return False
            # Create a datetime object to validate the date
            datetime.datetime(year, month, day)
            return True
        except ValueError:
            return False

   
    """func: collect pancard information"""
    def collect_pancard_info(self) -> dict:
        pancard_doc_info_list = []

        """Check Document mode"""
        if self.DOCUMENT_MODE == 1:

            """Collect: Pancard Number"""
            pancard_number = self.extract_pancard_number()
            if len(pancard_number['coordinates']) != 0:
                pancard_doc_info_list.append(pancard_number)
            else:
                pancard_doc_info_list.append(pancard_number)
                self.logger.error("| Pancard Number not found")

            """Collect: DOB"""
            dob = self.extract_dob()
            if len(dob['coordinates']) != 0:
                pancard_doc_info_list.append(dob)
            else:
                pancard_doc_info_list.append(dob)
                self.logger.error("| Pancard DOB not found")
            
            """Collect: Pancard username and father's name"""
            pattern_number = self.identify_pancard_pattern()
            if pattern_number == 1:
                matching_text_keyword_username = ["name", "uiname"]
                matching_text_keyword_fathername = ["father's name", "father", "/eather's"]

                username_p1 = PanCardPattern1(self.coordinates, self.text_data, matching_text_keyword_username, 1).extract_username_fathername_p1()
                fathername_p1 = PanCardPattern1(self.coordinates, self.text_data, matching_text_keyword_fathername, 2).extract_username_fathername_p1()

                if len(username_p1['coordinates']) != 0:
                    pancard_doc_info_list.append(username_p1)
                else:
                    pancard_doc_info_list.append(username_p1)
                    self.logger.error("| Pancard Username not found")

                if len(fathername_p1['coordinates']) != 0:
                    pancard_doc_info_list.append(fathername_p1)
                else:
                    pancard_doc_info_list.append(fathername_p1)
                    self.logger.error("| Pancard Father's name not found")
                
            else:
                username_p2 = PanCardPattern2(self.coordinates, self.text_data, 1).extract_username_p2()
                fathername_p2 = PanCardPattern2(self.coordinates, self.text_data, 2).extract_fathername_p2()
                
                if len(username_p2['coordinates']) != 0:
                    pancard_doc_info_list.append(username_p2)
                else:
                    pancard_doc_info_list.append(username_p2)
                    self.logger.error("| Pancard Username not found")

                if len(fathername_p2['coordinates']) != 0:
                    pancard_doc_info_list.append(fathername_p2)
                else:
                    pancard_doc_info_list.append(fathername_p2)
                    self.logger.error("| Pancard Father's name not found")
            
            """Collect: Signature"""
            if pattern_number == 1:
                user_signature = self.extract_signature(1)

                if len(user_signature['coordinates']) != 0:
                    pancard_doc_info_list.append(user_signature)
                else:
                    pancard_doc_info_list.append(user_signature)
                    self.logger.error("| Pancard Signature not found")
            else:
                user_signature = self.extract_signature(2)

                if len(user_signature['coordinates']) != 0:
                    pancard_doc_info_list.append(user_signature)
                else:
                    pancard_doc_info_list.append(user_signature)
                    self.logger.error("| Pancard Signature not found")
            
            """Collect: QR-Code"""
            qr_code = self.extract_qr_code()
            if len(qr_code['coordinates']) != 0:
                pancard_doc_info_list.append(qr_code)
            else:
                pancard_doc_info_list.append(qr_code)
                self.logger.error("| Pancard QR Code not found")

            """check pancard_doc_info_list"""
            if pattern_number == 1:
                all_lengths_zero = all(len(expression['coordinates']) == 0 for expression in [pancard_number, dob, username_p1, fathername_p1])
                if all_lengths_zero:
                    return {"message": "Unable to extract Pancard information", "status": "REJECTED"}
            else:
                all_lengths_zero = all(len(expression['coordinates']) == 0 for expression in [pancard_number, dob, username_p2, fathername_p2])
                if all_lengths_zero:
                    return {"message": "Unable to extract Pancard information", "status": "REJECTED"}

            
            all_keys_and_coordinates_empty =  all(all(not v for v in d.values()) for d in pancard_doc_info_list)
            if all_keys_and_coordinates_empty:
                return {"message": "Unable to extract Pancard information", "status": "REJECTED"}
            else:
                return {"message": "Successfully Redacted PAN Card Document", "status": "REDACTED", "data": pancard_doc_info_list}
        else:

            """Collect: Pancard Number"""
            pancard_number = self.extract_pancard_number()
            if len(pancard_number['coordinates']) == 0:
                self.logger.error("| Pancard Number not found")
                return {"message": "Unable to extract Pancard Number", "status": "REJECTED"}
            pancard_doc_info_list.append(pancard_number)

            """Collect: DOB"""
            dob = self.extract_dob()
            if len(dob['coordinates']) == 0:
                self.logger.error("| Pancard DOB not found")
                return {"message": "Unable to extract DOB from Pancard Document", "status": "REJECTED"}
            pancard_doc_info_list.append(dob)

            """Collect: Pancard username and father's name"""
            pattern_number = self.identify_pancard_pattern()
            if pattern_number == 1:
                matching_text_keyword_username = ["name", "uiname"]
                matching_text_keyword_fathername = ["father's name", "father", "/eather's"]
        
                username_p1 = PanCardPattern1(self.coordinates, self.text_data, matching_text_keyword_username, 1).extract_username_fathername_p1()
                fathername_p1 = PanCardPattern1(self.coordinates, self.text_data, matching_text_keyword_fathername, 2).extract_username_fathername_p1()
            
                if len(username_p1['coordinates']) == 0:
                    self.logger.error("| Pancard Username  not found")
                    return {"message": "Unable to extract Username from Pancard document", "status": "REJECTED"}
                pancard_doc_info_list.append(username_p1)

                if len(fathername_p1['coordinates']) == 0:
                    self.logger.error("| Pancard Father's name  not found")
                    return {"message": "Unable to extract Father's name from Pancard document", "status": "REJECTED"}
                pancard_doc_info_list.append(fathername_p1)
            else:
                username_p2 = PanCardPattern2(self.coordinates, self.text_data, 1).extract_username_p2()
                fathername_p2 = PanCardPattern2(self.coordinates, self.text_data, 2).extract_fathername_p2()

                if len(username_p2['coordinates']) == 0:
                    self.logger.error("| Pancard Username  not found")
                    return {"message": "Unable to extract Username from Pancard document", "status": "REJECTED"}
                pancard_doc_info_list.append(username_p2)

                if len(fathername_p2['coordinates']) == 0:
                    self.logger.error("| Pancard Father's name  not found")
                    return {"message": "Unable to extract Father's name from Pancard document", "status": "REJECTED"}
                pancard_doc_info_list.append(fathername_p2)
            
            """Collect: Signature"""
            if pattern_number == 1:
                user_signature = self.extract_signature(1)

                if len(user_signature['coordinates']) != 0:
                    pancard_doc_info_list.append(user_signature)
                else:
                    pancard_doc_info_list.append(user_signature)
                    self.logger.error("| Pancard Signature not found")
            else:
                user_signature = self.extract_signature(2)

                if len(user_signature['coordinates']) != 0:
                    pancard_doc_info_list.append(user_signature)
                else:
                    pancard_doc_info_list.append(user_signature)
                    self.logger.error("| Pancard Signature not found")
            
            """Collect: QR-Code"""
            qr_code = self.extract_qr_code()
            if len(qr_code['coordinates']) != 0:
                pancard_doc_info_list.append(qr_code)
            else:
                pancard_doc_info_list.append(qr_code)
                self.logger.error("| Pancard QR Code not found")

            return {"message": "Successfully Redacted PAN Card Document", "status": "REDACTED", "data": pancard_doc_info_list}