import pytesseract
import re
import configparser
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging
from helper.eaadhaarcard_text_coordinates import TextCoordinates

class CDSLInfo:
    def __init__(self, document_path: str) -> None:

        """Read config.ini"""
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(r'C:\Program Files (x86)\OCRR\config\config.ini')
        self.DOCUMENT_MODE = int(config['Mode']['ShowAvailableRedaction'])

        """Logger"""
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()

        """Get the coordinates of all the extracted text"""
        self.coordinates_default = TextCoordinates(document_path, lang_type="default").generate_text_coordinates()

        """Get the text from document"""
        self.text_data = pytesseract.image_to_string(document_path)

    """func: extract PANCARD number"""
    def extract_pancard_number(self):
        try:
            result = {
                "CDSL Pancard Number": "",
                "coordinates": []
            }
            pancard_text = ""
            pancard_coordinates = []

            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates_default):
                if len(text) == 10 and text.isupper() and text.isalnum():
                    pancard_text = text
                    pancard_coordinates = [x1, y1, x2, y2]
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
                "CDSL Pancard Number": "",
                "coordinates": []
            }
            return result


    """func: extract NAME"""
    def extract_name(self):
        try:
            result = {
                "CDSL Name": "",
                "coordinates": []
            }
            name_text = ""
            matching_text_coords = []
            next_line = []

            """split the text into lines"""
            lines = [i for i in self.text_data.splitlines() if len(i) != 0]

            """get the matching """
            pattern = r"\b(?:pan no)\b"
            for i, line in enumerate(lines):
                match = re.search(pattern, line.lower(), flags=re.IGNORECASE)
                if match:
                    next_line = lines[i + 1].split()
                    break
        
            if not next_line:
                return result

            for i in next_line:
                if i.lower() in ['name', ':']:
                    next_line.remove(i)

            name_text = " ".join(next_line)

            if len(next_line) > 1:
                next_line = next_line[:-1]                

            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates_default):
                if text in next_line:
                    matching_text_coords.append([x1, y1, x2, y2])
                if len(next_line) == len(matching_text_coords):
                    break
        
            if len(matching_text_coords) > 1:
                result = {
                    "CDSL Name": name_text,
                    "coordinates": [[matching_text_coords[0][0], matching_text_coords[0][1], matching_text_coords[-1][2], matching_text_coords[-1][3]]]
                }
            else:
                result = {
                    "CDSL Name": name_text,
                    "coordinates": [[matching_text_coords[0][0], matching_text_coords[0][1], matching_text_coords[0][2], matching_text_coords[0][3]]]
                }
            return result
        except Exception as error:
            result = {
                "CDSL Name": "",
                "coordinates": []
            }
            return result


    """func: collect CDSL info"""
    def collect_cdsl_info(self):
        cdsl_doc_info_list = []

        """Check Document mode"""
        if self.DOCUMENT_MODE == 1:

            """Collect: Pancard Number"""
            pancard_number = self.extract_pancard_number()
            if len(pancard_number['coordinates']) != 0:
                cdsl_doc_info_list.append(pancard_number)
            else:
                cdsl_doc_info_list.append(pancard_number)
                self.logger.error("| Pancard Number not found")

            """Collect: CDSL Name"""
            cdsl_name = self.extract_name()
            if len(cdsl_name['coordinates']) != 0:
                cdsl_doc_info_list.append(cdsl_name)
            else:
                cdsl_doc_info_list.append(cdsl_name)
                self.logger.error("| CDSL Name not found")

            """check cdsl_doc_info_list"""
            all_keys_and_coordinates_empty =  all(all(not v for v in d.values()) for d in cdsl_doc_info_list)
            if all_keys_and_coordinates_empty:
                return {"message": "Unable to extract CDSL information", "status": "REJECTED"}
            else:
                return {"message": "Successfully Redacted CDSL Document", "status": "REDACTED", "data": cdsl_doc_info_list}
            
        else:

            """Collect: Pancard Number"""
            pancard_number = self.extract_pancard_number()
            if len(pancard_number['coordinates']) == 0:
                self.logger.error("| CDSL Pancard Number not found")
                return {"message": "Unable to extract Pancard Number from CDSL", "status": "REJECTED"}
            cdsl_doc_info_list.append(pancard_number)

            """Collect: CDSL Name"""
            cdsl_name = self.extract_name()
            if len(cdsl_name['coordinates']) == 0:
                self.logger.error("| CDSL Name not found")
                return {"message": "Unable to extract Name from CDSL", "status": "REJECTED"}
            cdsl_doc_info_list.append(cdsl_name)
            
            return {"message": "Successfully Redacted CDSL Document", "status": "REDACTED", "data": cdsl_doc_info_list}