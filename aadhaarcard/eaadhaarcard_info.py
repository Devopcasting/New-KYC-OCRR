import pytesseract
import configparser
import re
import cv2
import datetime
from qreader import QReader
from config.indian_places import indian_states_cities
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging
from helper.eaadhaarcard_text_coordinates import TextCoordinates

class EaadhaarCardInfo:
    def __init__(self, document_path: str) -> None:

        self.document_path = document_path

        """Read config.ini"""
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(r'C:\Program Files (x86)\OCRR\config\config.ini')
        self.DOCUMENT_MODE = int(config['Mode']['ShowAvailableRedaction'])

        """Logger"""
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()

        self.coordinates_default = TextCoordinates(document_path, lang_type="default").generate_text_coordinates()
        self.coordinates_regional = TextCoordinates(document_path, lang_type="regional").generate_text_coordinates()
        self.coordinates = TextCoordinates(document_path).generate_text_coordinates()
        
        self.text_data_default = pytesseract.image_to_string(document_path)
        self.text_data_regional = pytesseract.image_to_string(document_path, lang="hin+eng")

        self.states = indian_states_cities
        
        # Create a QReader instance
        self.qreader = QReader()
    
    """func: extract dob"""
    def extract_dob(self) -> dict:
        try:
            result = {
                "Aadhaar DOB": "",
                "coordinates": []
            }
            dob_text = ""
            dob_coordinates = []

            """Data patterns: DD/MM/YYY, DD-MM-YYY"""
            date_pattern = r'\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}|\d{4}'

            for i, (x1, y1, x2, y2, text) in enumerate(self.coordinates_default):
                match = re.search(date_pattern, text)
                if match:
                    if self.validate_date(text, '/'):
                        dob_coordinates = [x1, y1, x2, y2]
                        dob_text += " "+text
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
            result = {
                "Aadhaar DOB": "",
                "coordinates": []
            }
            return result

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

    """func: extract gender"""
    def extract_gender(self):
        try:
            result = {
                "Aadhaar Gender": "",
                "coordinates": []
            }
            gender_text = ""
            gender_coordinates = []

            """get the index number of Male/Female"""
            matching_index = 0
            for i ,(x1,y1,x2,y2,text) in enumerate(self.coordinates_default):
                if text.lower() in ["male", "female"]:
                    matching_index = i
                    gender_text = text
                    break
            if matching_index == 0:
                return result
        
            """reverse loop from Male/Female index until DOB comes"""
            for i in range(matching_index, -1, -1):
                if re.match(r'^\d{2}/\d{2}/\d{4}$', self.coordinates_default[i][4]) or re.match(r'^\d{4}$', self.coordinates_default[i][4]):
                    break
                else:
                    gender_coordinates.append([self.coordinates_default[i][0], self.coordinates_default[i][1], 
                                           self.coordinates_default[i][2], self.coordinates_default[i][3]])
        
            result = {
                "Aadhaar Gender": gender_text,
                "coordinates": [[gender_coordinates[-1][0], gender_coordinates[-1][1], gender_coordinates[0][2], gender_coordinates[0][3]]]
            }
            return result
        except Exception as error:
            result = {
                "Aadhaar Gender": "",
                "coordinates": []
            }
            return result

    """func: extract aadhaar card number"""
    def extract_aadhaarcard_number(self):
        try:
            result = {
                "Aadhaar Number": "",
                "coordinates": []
                }
            aadhaarcard_text = ""
            aadhaarcard_coordinates = []
            text_coordinates = []

            """get the index of male/female"""
            matching_index = 0
            for i,(x1,y1,x2,y2,text) in enumerate(self.coordinates):
                if text.lower() in ["male", "female"]:
                    matching_index = i
            if matching_index == 0:
                return result
        
            """get the coordinates of aadhaar card number"""
            for i in range(matching_index, len(self.coordinates)):
                text = self.coordinates[i][4]
                if len(text) == 4 and text.isdigit() and text[:2] != '19':
                    text_coordinates.append((text))
                    aadhaarcard_text += ' '+ text
                if len(text_coordinates) == 3:
                    break
        
            for i in text_coordinates[:-1]:
                for k,(x1,y1,x2,y2,text) in enumerate(self.coordinates):
                    if i in text:
                        aadhaarcard_coordinates.append([x1, y1, x2, y2])
            result = {
                "Aadhaar Number": aadhaarcard_text,
                "coordinates": aadhaarcard_coordinates
            }
            return result
        except Exception as error:
            result = {
                "Aadhaar Number": "",
                "coordinates": []
                }
            return result

    """func: extract name in english"""
    def extract_name_in_english(self):
        try:
            result = {
                "Aadhaar Name": "",
                "coordinates": []
            }
            name_coordinates = []

            """get clean text list"""
            clean_text = [i for i in self.text_data_default.split("\n") if len(i) != 0]

            """get the above matching text"""
            matching_text = []
            for i,text in enumerate(clean_text):
                if "dob" in text.lower() or "birth" in text.lower() or "bith" in text.lower() or "year" in text.lower() or "binh" in text.lower():
                    matching_text = clean_text[i - 1].split()
                    break
            if not matching_text:
                return result
            
            clean_matching_text = [i for i in matching_text if i.isalpha()]

            if len(clean_matching_text) > 1:
                clean_matching_text = clean_matching_text[:-1]
        
            for i, (x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if text in clean_matching_text:
                    name_coordinates.append([x1, y1, x2, y2])
        
            result = {
                "Aadhaar Name": " ".join(clean_matching_text),
                "coordinates": name_coordinates
            }
        
            return result
        except Exception as error:
            result = {
                "Aadhaar Name": "",
                "coordinates": []
            }
            return result

    """func: extract name in regional language"""
    def extract_name_in_regional(self):
        try:
            result = {
                "Aadhaar Regional Name": "",
                "coordinates": []
                }
            name_coordinates = []

            """get clean text list"""
            clean_text = [i for i in self.text_data_regional.split("\n") if len(i) != 0]

            """get the above matching text"""
            matching_text = []
            keywords_regex = r"\b(?:dob|birth|bith|year|binh|008)\b"
            for i,text in enumerate(clean_text):
                if re.search(keywords_regex, text.lower(), flags=re.IGNORECASE):
                    matching_text = clean_text[i - 2].split()
                    break
            if not matching_text:
                return result
        
            if len(matching_text) > 1:
                matching_text = matching_text[:-1]
        
            for i, (x1, y1, x2, y2, text) in enumerate(self.coordinates_regional):
                if text in matching_text:
                    name_coordinates.append([x1, y1, x2, y2])
        
            result = {
                "Aadhaar Regional Name": " ".join(matching_text),
                "coordinates": name_coordinates
            }

            return result
        except Exception as error:
            result = {
                "Aadhaar Regional Name": "",
                "coordinates": []
                }
            return result

    """func: extract mobile number"""
    def extract_mobile_number(self):
        try:
            result = {
                "Aadhaar Mobile Number": "",
                "coordinates": []
            }
            mobile_number = ""
            mobile_coordinates = []

            """get the coordinates"""
            for i,(x1, y1, x2, y2,text) in enumerate(self.coordinates):
                if len(text) == 10 and text.isdigit():
                    mobile_coordinates = [x1, y1, x2, y2]
                    mobile_number = text
                    break
            if not mobile_coordinates:
                return result
        
            """get first 6 chars"""
            width = mobile_coordinates[2] - mobile_coordinates[0]
            result = {
                "Aadhaar Mobile Number" : mobile_number,
                "coordinates" : [[mobile_coordinates[0], mobile_coordinates[1], mobile_coordinates[0] + int(0.54 * width), mobile_coordinates[3]]]
            }
            return result
        except Exception as error:
            result = {
                "Aadhaar Mobile Number": "",
                "coordinates": []
            }
            return result


    """func: extract pin code"""
    def extract_pin_code(self):
        try:
            result = {
                "Aadhaar Pincode": "",
                "coordinates": []
            }
            pin_code = ""
            pin_code_coordinates = []
            get_coords_result = []

            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
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
            result = {
                "Aadhaar Pincode": "",
                "coordinates": []
            }
            return result

    """"func: extract state name"""
    def extract_state_name(self):
        try:
            result = {
                "Aadhaar Place Name": "",
                "coordinates": []
            }
            state_name = ""
            state_coordinates = []

            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
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
            result = {
                "Aadhaar Place Name": "",
                "coordinates": []
            }
            return result

    """func: extract QR code"""
    def extract_qr_code(self):
        try:
            result = {
                "Aadhaar QR Code": "",
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
                "Aadhaar QR Code": "",
                "coordinates": []
            }
            return result


    """func: get first 3 chars"""
    def get_first_3_chars(self, coords: list) -> list:
        width = coords[2] - coords[0]
        result = [coords[0], coords[1], coords[0] + int(0.30 * width), coords[3]]
        return result

    """func: collect e-aadhaar card info"""
    def collect_eaadhaarcard_info(self) -> dict:
        eaadhaarcard_doc_info_list = []

        """Check Document mode"""
        if self.DOCUMENT_MODE == 1:
             
            """Collect: Name in regional"""
            name_in_regional = self.extract_name_in_regional()
            if len(name_in_regional['coordinates']) != 0 :
                eaadhaarcard_doc_info_list.append(name_in_regional)
            else:
                eaadhaarcard_doc_info_list.append(name_in_regional)
                self.logger.error("| E-Aadhaar Card Name in regional language not found")
                
            """Collect: Name in english"""
            name_in_english = self.extract_name_in_english()
            if len(name_in_english['coordinates']) != 0:
                eaadhaarcard_doc_info_list.append(name_in_english)
            else:
                eaadhaarcard_doc_info_list.append(name_in_english)
                self.logger.error("| E-Aadhaar Card Name in english not found")
            
            """Collect: DOB"""
            dob = self.extract_dob()
            if len(dob['coordinates']) != 0:
                eaadhaarcard_doc_info_list.append(dob)
            else:
                eaadhaarcard_doc_info_list.append(dob)
                self.logger.error("| E-Aadhaar Card DOB not found")

            """Collect: Gender"""
            gender = self.extract_gender()
            if len(gender['coordinates']) != 0:
                eaadhaarcard_doc_info_list.append(gender)
            else:
                eaadhaarcard_doc_info_list.append(gender)
                self.logger.error("| E-Aadhaar Card Gender not found")
            
            """Collect: Aadhaar Card Number"""
            aadhaarcard_number = self.extract_aadhaarcard_number()
            if len(aadhaarcard_number['coordinates']) != 0:
                eaadhaarcard_doc_info_list.append(aadhaarcard_number)
            else:
                eaadhaarcard_doc_info_list.append(aadhaarcard_number)
                self.logger.error("| E-Aadhaar Card Number not found")
            
            """Collect: Mobile Number"""
            mobile_number = self.extract_mobile_number()
            if len(mobile_number['coordinates']) != 0:
                eaadhaarcard_doc_info_list.append(mobile_number)
            else:
                eaadhaarcard_doc_info_list.append(mobile_number)
                self.logger.error("| E-Aadhaar Mobile Number not found")

            """Collect: Pin Code"""
            pincode = self.extract_pin_code()
            if len(pincode['coordinates']) != 0:
                eaadhaarcard_doc_info_list.append(pincode)
            else:
                eaadhaarcard_doc_info_list.append(pincode)
                self.logger.error("| E-Aadhaar Pincode not found")
            
            """Collect: State name"""
            state = self.extract_state_name()
            if len(state['coordinates']) != 0:
                eaadhaarcard_doc_info_list.append(state)
            else:
                eaadhaarcard_doc_info_list.append(state)
                self.logger.error("| E-Aadhaar State name not found")
            
            """Collect: QR-Code"""
            qr_code = self.extract_qr_code()
            if len(qr_code['coordinates']) != 0:
                eaadhaarcard_doc_info_list.append(qr_code)
            else:
                eaadhaarcard_doc_info_list.append(qr_code)
                self.logger.error("| E-Aadhaar QR Code not found")


            """"check eaadhaarcard_doc_info_list"""
            all_keys_and_coordinates_empty =  all(all(not v for v in d.values()) for d in eaadhaarcard_doc_info_list)
            if all_keys_and_coordinates_empty:
                return {"message": "Unable to extract E-Aadhaar information", "status": "REJECTED"}
            else:
                return {"message": "Successfully Redacted E-Aadhaar Card Document", "status": "REDACTED", "data": eaadhaarcard_doc_info_list}

        else:

            """Collect: Name in regional"""
            name_in_regional = self.extract_name_in_regional()
            if len(name_in_regional['coordinates']) == 0:
                self.logger.error("| E-Aadhaar Card Name in regional language not found")
                return {"message": "Unable to extract name in regional from E-Aadhaar Document", "status": "REJECTED"}
            eaadhaarcard_doc_info_list.append(name_in_regional)

            """Collect: Name in english"""
            name_in_english = self.extract_name_in_english()
            if len(name_in_english['coordinates']) == 0:
                self.logger.error("| E-Aadhaar Card Name in english not found")
                return {"message": "Unable to extract name in english from E-Aaadhaar Document", "status": "REJECTED"}
            eaadhaarcard_doc_info_list.append(name_in_english)

            """Collect: DOB"""
            dob = self.extract_dob()
            if len(dob['coordinates']) == 0:
                self.logger.error("| E-Aadhaar Card DOB not found")
                return {"message": "Unable to extract DOB from E-Aadhaar Document", "status": "REJECTED"}
            eaadhaarcard_doc_info_list.append(dob)

            """Collect: Gender"""
            gender = self.extract_gender()
            if len(gender['coordinates']) == 0:
                self.logger.error("| E-Aadhaar Card Gender not found")
                return {"message": "Unable to extract gender from E-Aadhaar Document", "status": "REJECTED"}
            eaadhaarcard_doc_info_list.append(gender)

            """Collect: Aadhaar Card Number"""
            aadhaarcard_number = self.extract_aadhaarcard_number()
            if len(aadhaarcard_number['coordinates']) == 0:
                self.logger.error("| E-Aadhaar Card Number not found")
                return {"message": "Unable to extract aadhaar card number", "status": "REJECTED"}
            eaadhaarcard_doc_info_list.append(aadhaarcard_number)

            """Collect: Mobile Number"""
            mobile_number = self.extract_mobile_number()
            if len(mobile_number['coordinates']) == 0:
                self.logger.error("| E-Aadhaar Mobile Number not found")
                return {"message": "Unable to extract aadhaar mobile number", "status": "REJECTED"}
            eaadhaarcard_doc_info_list.append(mobile_number)

            """Collect: Pin Code"""
            pincode = self.extract_pin_code()
            if len(pincode['coordinates']) == 0:
                self.logger.error("| E-Aadhaar Card Pincode not found")
                return {"message": "Unable to extract aadhaar pincode", "status": "REJECTED"}
            eaadhaarcard_doc_info_list.append(pincode)
            
            """Collect: QR Code"""
            qr_code = self.extract_qr_code()
            if len(qr_code['coordinates']) == 0:
                self.logger.error("| E-Aadhaar QR-Code not found")
                return {"message": "Unable to extract aadhaar QR-Code", "status": "REJECTED"}

            eaadhaarcard_doc_info_list.append(qr_code)
        
            return {"message": "Successfully Redacted E-Aadhaar Card Document", "status": "REDACTED", "data": eaadhaarcard_doc_info_list}
