import pytesseract
import configparser
import re
from config.indian_places import indian_states_cities
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging
from helper.dl_text_coordinates import TextCoordinates

class DrivingLicenseDocumentInfo:
    def __init__(self, document_path) -> None:

        """Read config.ini"""
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(r'C:\Program Files (x86)\OCRR\config\config.ini')
        self.DOCUMENT_MODE = int(config['Mode']['ShowAvailableRedaction'])

        """Logger"""
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()

        """Get the coordinates of all the extracted text"""
        self.coordinates = TextCoordinates(document_path).generate_text_coordinates()

        """Get the text from document"""
        self.text_data = pytesseract.image_to_string(document_path, lang="eng")

        """List of states"""
        self.states = indian_states_cities

    """func: extract driving license number"""
    def extract_dl_number(self):
        try:
            result = {
                "Driving License Number": "",
                "coordinates": []    
            }
            dl_number = ""
            dl_number_coordinated = []

            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if len(text) == 11 and text.isdigit():
                    dl_number = text
                    dl_number_coordinated.append([x1, y1, x2, y2])
                    break
            if not dl_number_coordinated:
                return result
        
            result = {
                "Driving License Number": dl_number,
                "coordinates": dl_number_coordinated
            }
            return result
        except Exception as error:
            result = {
                "Driving License Number": "",
                "coordinates": []    
            }
            return result
            
    """func: extract dates"""
    def extract_dates(self):
        try:
            result = {
                "Driving License Dates": "",
                "coordinates": []
            }
            date_text = ""
            date_coords = []
            date_coordinates = []

            """date pattern"""
            date_pattern = r'\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}'

            """get the coordinates"""
            for i, (x1,y1,x2,y2,text) in enumerate(self.coordinates):
                date_match = re.search(date_pattern, text)
                if date_match:
                    date_coords.append([x1, y1, x2, y2])
                    date_text += " "+ text
        
            if not date_coords:
                return result
        
            """get the first 6 chars"""
            for i in date_coords:
                width = i[2] - i[0]
                date_coordinates.append([i[0], i[1], i[0] + int(0.54 * width), i[3]])
        
            result = {
                "Driving License Dates": date_text,
                "coordinates": date_coordinates
            }
            return result
        except Exception as error:
            result = {
                "Driving License Dates": "",
                "coordinates": []
            }
            return result

    
    """func: extract pincode"""
    def extract_pincode(self):
        try:
            result = {
                "Driving License Pincode": "",
                "coordinates": []
            }
            pincode_number = ""
            pincode_coordinates = []
            pincode_coords = []

            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if len(text) == 6 and text.isdigit():
                    pincode_coords.append([x1, y1, x2, y2])
                    pincode_number += " "+text
                    break
            if not pincode_coords:
                return result
            
            for i in pincode_coords:
                width = i[2] - i[0]
                pincode_coordinates.append([i[0], i[1], i[0] + int(0.30 * width), i[3]])
        
            result = {
                "Driving License Pincode": pincode_number,
                "coordinates": pincode_coordinates
            }
            return result
        except Exception as error:
            result = {
                "Driving License Pincode": "",
                "coordinates": []
            }
            return result

    
    """func: extract state"""
    def extract_state(self):
        try:
            result = {
                "Driving License Place": "",
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
                "Driving License Place": state_name,
                "coordinates": state_coordinates
            }
            return result
        except Exception as error:
            result = {
                "Driving License Place": "",
                "coordinates": []
            }
            return result

    
    """func: extract name"""
    def extract_name(self):
        try:
            result = {
                "Driving License Name": "",
                "coordinates": []
            }
            name_text = ""
            name_coords = []
            matching_text = r"\b(?:name)\b"
            matching_text_index = 0

            """get matching text index"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if re.search(matching_text, text.lower(), flags=re.IGNORECASE):
                    matching_text_index = i
                    break
        
            if not matching_text_index:
                return result

            """get the coordinates"""
            for i in range(matching_text_index + 1, len(self.coordinates)):
                text = self.coordinates[i][4]
                if text.lower() in ['s/dmw', 'dmw', 's/']:
                    break
                name_coords.append([x1, y1, x2, y2])
                name_text += " "+text
        
            if len(name_coords) > 1:
                result = {
                    "Driving License Name": name_text,
                    "coordinates": [[name_coords[0][0], name_coords[0][1], name_coords[-1][2], name_coords[-1][3]]]
                }
            else:
                result = {
                    "Driving License Name": name_text,
                    "coordinates": [[name_coords[0][0], name_coords[0][1], name_coords[0][2], name_coords[0][3]]]
                }
        
            return result
        except Exception as error:
            result = {
                "Driving License Name": "",
                "coordinates": []
            }
            return result

    
    """func: collect DL information"""
    def collect_dl_info(self):
        dl_card_info_list = []

        """Check Document mode"""
        if self.DOCUMENT_MODE == 1:

            """Collect DL number"""
            dl_number = self.extract_dl_number()
            if len(dl_number['coordinates']) != 0:
                dl_card_info_list.append(dl_number)
            else:
                dl_card_info_list.append(dl_number)
                self.logger.error("| Driving license number not found")
        
            """Collect DL dates"""
            dl_dates = self.extract_dates()
            if len(dl_dates['coordinates']) != 0:
                dl_card_info_list.append(dl_dates)
            else:
                dl_card_info_list.append(dl_dates)
                self.logger.error("| Driving license dates not found")

            """Collect DL pincode"""
            dl_pincode = self.extract_pincode()
            if len(dl_pincode['coordinates']) != 0:
                dl_card_info_list.append(dl_pincode)
            else:
                dl_card_info_list.append(dl_pincode)
                self.logger.error("| Driving license Pincode not found")
            
            """Collect DL State"""
            dl_state = self.extract_state()
            if len(dl_state['coordinates']) != 0:
                dl_card_info_list.append(dl_state)
            else:
                dl_card_info_list.append(dl_state)
                self.logger.error("| Driving license State name not found")
            
            """Collect DL name"""
            dl_name = self.extract_name()
            if len(dl_name['coordinates']) != 0:
                dl_card_info_list.append(dl_name)
            else:
                dl_card_info_list.append(dl_name)
                self.logger.error("| Driving license name not found")


            """check dl_card_info_list"""
            all_keys_and_coordinates_empty =  all(all(not v for v in d.values()) for d in dl_card_info_list)
            if all_keys_and_coordinates_empty:
                return {"message": "Unable to extract driving license information", "status": "REJECTED"}
            else:
                return {"message": "Successfully Redacted Driving License Document", "status": "REDACTED", "data": dl_card_info_list}

        else:
        
            """Collect DL number"""
            dl_number = self.extract_dl_number()
            if len(dl_number['coordinates']) == 0:
                self.logger.error("| Driving license number not found")
                return {"message": "Unable to extract driving license number", "status": "REJECTED"}
            dl_card_info_list.append(dl_number)

            """Collect DL dates"""
            dl_dates = self.extract_dates()
            if len(dl_dates['coordinates']) == 0:
                self.logger.error("| Driving license dates not found")
                return {"message": "Unable to extract dates from license number", "status": "REJECTED"}
            dl_card_info_list.append(dl_dates)
        
            """Collect DL pincode"""
            dl_pincode = self.extract_pincode()
            if len(dl_pincode["coordinates"]) == 0:
                self.logger.error("| Driving license pincode not found")
                return {"message": "Unable to extract pincode from driving license number", "status": "REJECTED"}
            dl_card_info_list.append(dl_pincode)

            """Collect DL State"""
            dl_state = self.extract_state()
            if len(dl_state['coordinates']) == 0:
                self.logger.error("| Driving license place not found")
                return {"message": "Unable to extract place from driving license number", "status": "REJECTED"}
            dl_card_info_list.append(dl_state)

            """Collect DL name"""
            dl_name = self.extract_name()
            if len(dl_name['coordinates']) == 0:
                self.logger.error("| Driving license name not found")
                return {"message": "Unable to extract name from driving license number", "status": "REJECTED"}
            dl_card_info_list.append(dl_name)

            return {"message": "Successfully Redacted Driving License Document", "status": "REDACTED", "data": dl_card_info_list}