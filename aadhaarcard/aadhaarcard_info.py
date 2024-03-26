import pytesseract
import configparser
import re
import cv2
from qreader import QReader
from config.indian_places import indian_states_cities
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging
from helper.eaadhaarcard_text_coordinates import TextCoordinates

class AaadhaarCardInfo:
    def __init__(self, document_path: str) -> None:
        
        self.document_path = document_path

        """Read config.ini"""
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(r'C:\Program Files (x86)\OCRR\config\config.ini')
        self.DOCUMENT_MODE = int(config['Mode']['ShowAvailableRedaction'])

        """Logger"""
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()

        """Get coordinates"""
        self.coordinates_default = TextCoordinates(document_path, lang_type="default").generate_text_coordinates()
        self.coordinates_regional = TextCoordinates(document_path, lang_type="regional").generate_text_coordinates()

        """Get String"""
        tesseract_config = r'--oem 3 --psm 11'
        self.text_data_default = pytesseract.image_to_string(document_path)
        self.text_data_regional = pytesseract.image_to_string(document_path, lang="hin+eng", config=tesseract_config)

        self.states = indian_states_cities

        # Create a QReader instance
        self.qreader = QReader()

    """func: extract DOB"""
    def extract_dob(self):
        result = {
            "Aadhaar DOB": "",
            "coordinates": []
            }
        try:
            dob_text = ""
            dob_coordinates = []
        
            """Data patterns: DD/MM/YYY, DD-MM-YYY"""
            date_pattern = r'\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}|\d{4}'

            for i, (x1, y1, x2, y2, text) in enumerate(self.coordinates_default):
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
                "Aadhaar DOB": dob_text,
                "coordinates": [[dob_coordinates[0], dob_coordinates[1], dob_coordinates[0] + int(0.54 * width), dob_coordinates[3]]]
            }
            return result
        except Exception as error:
            self.logger.error(f"Error: Aadhaar DOB | {error}")
            return result

    """func: extract Gender"""
    def extract_gender(self):
        result = {
            "Aadhaar Gender": "",
            "coordinates": []
            }
        try:
            gender_text = ""
            gender_coordinates = []

            gender_pattern = r"male|female"
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates_default):
                if re.search(gender_pattern, text, flags=re.IGNORECASE):
                    gender_coordinates.append([x1, y1, x2, y2])
                    gender_text = text
                    break
            if not gender_coordinates:
                return result
            
            result = {
                "Aadhaar Gender": gender_text,
                "coordinates": gender_coordinates
            }
            return result
        except Exception as error:
            self.logger.error(f"Error: Aadhaar Gender | {error}")
            return result

    
    """func: extact aadhaar card number"""
    def extract_aadhaar_number(self):
        result = {
            "Aadhaar Number": "",
            "coordinates": []
            }
        try:
            aadhaarcard_text = ""
            aadhaarcard_coordinates = []
            text_coordinates = []

            """get the index of male/female"""
            matching_index = 0
            gender_pattern = r"male|female"
            for i,(x1,y1,x2,y2,text) in enumerate(self.coordinates_default):
                if re.search(gender_pattern, text, flags=re.IGNORECASE):
                    matching_index = i

            if matching_index == 0:
                return result
        
            """get the coordinates of aadhaar card number"""
            for i in range(matching_index, len(self.coordinates_default)):
                text = self.coordinates_default[i][4]
                if len(text) == 4 and text.isdigit() and text[:2] != '19':
                    text_coordinates.append((text))
                    aadhaarcard_text += ' '+ text
                if len(text_coordinates) == 3:
                    break
        
            for i in text_coordinates[:-1]:
                for k,(x1,y1,x2,y2,text) in enumerate(self.coordinates_default):
                    if i in text:
                        aadhaarcard_coordinates.append([x1, y1, x2, y2])

            result = {
                "Aadhaar Number": aadhaarcard_text,
                "coordinates": aadhaarcard_coordinates
            }
            return result
        except Exception as error:
            self.logger.error(f"Error: Aadhaar Number | {error}")
            return result

    
    """func: extract name"""
    def extract_name(self):
        result = {
            "Aadhaar Name": "",
            "coordinates": []
            }
        try:
            name_text = ""
            name_coordinates = []

            """split the text into lines"""
            lines = [i for i in self.text_data_default.splitlines() if len(i) != 0]
        
            """regex patterns"""
            dob_pattern = re.compile(r"DOB", re.IGNORECASE)
            date_pattern = re.compile(r"\d{1,2}/\d{1,2}/\d{4}")
            year_pattern = re.compile(r"\d{4}")

            """get the matching text index"""
            for i, item in enumerate(lines):
                if dob_pattern.search(item) or date_pattern.search(item) or year_pattern.search(item):
                    name_text = lines[i - 1]
                    break
            if not name_text:
                return result
        
            """split the name"""
            name_text_split = name_text.split()
            if len(name_text_split) > 1:
                name_text_split = name_text_split[:-1]
        
            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates_default):
                if text in name_text_split:
                    name_coordinates.append([x1, y1, x2, y2])
                if len(name_text_split) == len(name_coordinates):
                    break
        
            if len(name_text_split) > 1:
                result = {
                    "Aadhaar Name": name_text,
                    "coordinates": [[name_coordinates[0][0], name_coordinates[0][1], name_coordinates[-1][2], name_coordinates[-1][3]]]
                }
            else:
                result = {
                    "Aadhaar Name": name_text,
                    "coordinates": [[name_coordinates[0][0], name_coordinates[0][1], name_coordinates[0][2], name_coordinates[0][3]]]
            }
            return result
        except Exception as error:
            self.logger.error(f"Error: Aadhaar Name | {error}")
            return result

    """func: extract name in regional lang"""
    def extract_name_in_regional(self):
        result = {
            "Aadhaar Name": "",
            "coordinates": []
            }
        try:
            name_text = ""
            name_coordinates = []

            """split the text into lines"""
            lines = [i for i in self.text_data_regional.splitlines() if len(i) != 0]

            """get the matching text index"""
            gender_pattern = r"male|female"
            for i, item in enumerate(lines):
                if re.search(gender_pattern, item, flags=re.IGNORECASE):
                    name_text = lines[i - 2]
                    break
            if not name_text:
                return result
        
            """split the name"""
            name_text_split = name_text.split()
            if len(name_text_split) > 1:
                name_text_split = name_text_split[:-1]
        
            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates_regional):
                if text in name_text_split:
                    name_coordinates.append([x1, y1, x2, y2])
                if len(name_text_split) == len(name_coordinates):
                    break
        
            if len(name_text_split) > 1:
                result = {
                    "Aadhaar Name": name_text,
                    "coordinates": [[name_coordinates[0][0], name_coordinates[0][1], name_coordinates[-1][2], name_coordinates[-1][3]]]
                }
            else:
                result = {
                    "Aadhaar Name": name_text,
                    "coordinates": [[name_coordinates[0][0], name_coordinates[0][1], name_coordinates[0][2], name_coordinates[0][3]]]
                }
            return result
        except Exception as error:
            self.logger.error(f"Error: Aadhaar Name | {error}")
            return result

    """"func: extract state name"""
    def extract_state_name(self):
        result = {
            "Aadhaar Place Name": "",
            "coordinates": []
            }
        try:
            state_name = ""
            state_coordinates = []

            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates_default):
                for state_pattern in self.states:
                    if re.search(state_pattern, text, re.IGNORECASE):
                        state_coordinates.append([x1, y1, x2, y2])
                        state_name = text
                        break
            if not state_coordinates:
                return result
        
            result = {
                "Aadhaar Place Name": state_name,
                "coordinates": state_coordinates
            }

            return result
        except Exception as error:
            self.logger.error(f"Error: Aadhaar Place Name | {error}")
            return result
        
    """func: extract pin code"""
    def extract_pin_code(self):
        result = {
            "Aadhaar Pincode": "",
            "coordinates": []
            }
        try:
            pin_code = ""
            pin_code_coordinates = []
            get_coords_result = []

            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates_default):
                if len(text) == 6 and text.isdigit():
                    pin_code_coordinates.append([x1, y1, x2, y2])
                    pin_code = text
            if not pin_code_coordinates:
                return result
        
            for i in pin_code_coordinates:
                coords_result = self.get_first_3_chars(i)
                get_coords_result.append(coords_result)

            result = {
                "Aadhaar Pincode": pin_code,
                "coordinates": get_coords_result
            }
            return result
        except Exception as error:
            self.logger.error(f"Error: Aadhaar Pincode | {error}")
            return result

    
    """func: extract QR code"""
    def extract_qr_code(self):
        result = {
            "Aadhaar QR Code": "",
            "coordinates": []
            }
        try:
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
                "Aadhaar QR-Code": f"Found {len(qrcode_coordinates)} QR Codes",
                "coordinates": qrcode_coordinates
            }
            return result
        except Exception as error:
            self.logger.error(f"Error: Aadhaar QR-Code | {error}")
            return result

    """func: get first 3 chars"""
    def get_first_3_chars(self, coords: list) -> list:
        width = coords[2] - coords[0]
        result = [coords[0], coords[1], coords[0] + int(0.30 * width), coords[3]]
        return result

    """func: collect aadhaar card info"""
    def collect_aadhaarcard_info(self) -> dict:
        aadhaarcard_doc_info_list = []

        """Check Document mode"""
        if self.DOCUMENT_MODE == 1:

            """Collect: DOB"""
            dob = self.extract_dob()
            if len(dob['coordinates']) != 0:
                aadhaarcard_doc_info_list.append(dob)
            else:
                aadhaarcard_doc_info_list.append(dob)
                self.logger.error("| Aadhaar Card DOB not found")

            """Collect: Gender"""
            gender = self.extract_gender()
            if len(gender['coordinates']) != 0:
                aadhaarcard_doc_info_list.append(gender)
            else:
                self.logger.error("| Aadhaar Card Gender not found")
                aadhaarcard_doc_info_list.append(gender)

            """Collect: Aadhaar card number"""
            aadhaar_card_number = self.extract_aadhaar_number()
            if len(aadhaar_card_number['coordinates']) != 0:
                aadhaarcard_doc_info_list.append(aadhaar_card_number)
            else:
                self.logger.error("| Aadhaar Card Number not found")
                aadhaarcard_doc_info_list.append(aadhaar_card_number)
            
            """Collect: Name"""
            name = self.extract_name()
            if len(name['coordinates']) != 0:
                aadhaarcard_doc_info_list.append(name)
            else:
                self.logger.error("| Aadhaar Card name not found")
                aadhaarcard_doc_info_list.append(name)

            """Collect: Name in Regional lang"""
            regional_name = self.extract_name_in_regional()
            if len(regional_name['coordinates']) != 0:
                aadhaarcard_doc_info_list.append(regional_name)
            else:
                self.logger.error("| Aadhaar Card name in regional language not found")
                aadhaarcard_doc_info_list.append(regional_name)

            """Collect: State name"""
            state_name = self.extract_state_name()
            if len(state_name['coordinates']) != 0:
                aadhaarcard_doc_info_list.append(state_name)
            else:
                self.logger.error("| Aadhaar Card State name not found")
                aadhaarcard_doc_info_list.append(state_name)
            
            """Collect: State Pin code"""
            state_pin_code = self.extract_pin_code()
            if len(state_pin_code['coordinates']) != 0:
                aadhaarcard_doc_info_list.append(state_pin_code)
            else:
                self.logger.error("| Aadhaar Card State code not found")
                aadhaarcard_doc_info_list.append(state_pin_code)
            
            """Collect: QR-Code"""
            qr_code = self.extract_qr_code()
            if len(qr_code['coordinates']) != 0:
                aadhaarcard_doc_info_list.append(qr_code)
            else:
                self.logger.error("| Aadhaar Card QR-Code not found")
                aadhaarcard_doc_info_list.append(qr_code)
            

            """"check eaadhaarcard_doc_info_list"""
            all_keys_and_coordinates_empty =  all(all(not v for v in d.values()) for d in aadhaarcard_doc_info_list)
            if all_keys_and_coordinates_empty:
                return {"message": "Unable to extract Aadhaar information", "status": "REJECTED"}
            else:
                return {"message": "Successfully Redacted Aadhaar Card Document", "status": "REDACTED", "data": aadhaarcard_doc_info_list}

        else:
            """Collect: DOB"""
            dob = self.extract_dob()
            if len(dob['coordinates']) != 0:
                aadhaarcard_doc_info_list.append(dob)
            else:
                self.logger.error("| Aadhaar Card DOB not found")
                return {"message": "Unable to extract DOB from Aadhaar Document", "status": "REJECTED"}

            """Collect: Gender"""
            gender = self.extract_gender()
            if len(gender['coordinates']) != 0:
                aadhaarcard_doc_info_list.append(gender)
            else:
                self.logger.error("| Aadhaar Card Gender not found")
                return {"message": "Unable to extract Gender from Aadhaar Document", "status": "REJECTED"}

            """Collect: Aadhaar card number"""
            aadhaar_card_number = self.extract_aadhaar_number()
            if len(aadhaar_card_number["coordinates"]) != 0:
                aadhaarcard_doc_info_list.append(aadhaar_card_number)
            else:
                self.logger.error("| Aadhaar Card Number not found")
                return {"message": "Unable to extract Aadhaar Number", "status": "REJECTED"}
            
            """Collect: Name"""
            name = self.extract_name()
            if len(name['coordinates']) != 0:
                aadhaarcard_doc_info_list.append(name)
            else:
                self.logger.error("| Aadhaar Card name not found")
                return {"message": "Unable to extract Aadhaar Name", "status": "REJECTED"}
            
            """Collect: Name in Regional lang"""
            regional_name = self.extract_name_in_regional()
            if len(regional_name['coordinates']) != 0:
                aadhaarcard_doc_info_list.append(regional_name)
            else:
                self.logger.error("| Aadhaar Card name in regional language not found")
                return {"message": "Unable to extract Aadhaar Name in regional language", "status": "REJECTED"}
            
            return {"message": "Successfully Redacted Aadhaar Card Document", "status": "REDACTED", "data": aadhaarcard_doc_info_list}


