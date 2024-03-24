import re
import pytesseract
import configparser
from config.indian_places import indian_states_cities
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging
from helper.passport_text_coordinates import TextCoordinates

class PassportDocumentInfo:
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
        tesseract_config = r'--oem 3 --psm 11'
        self.text_data = pytesseract.image_to_string(document_path, lang="eng", config=tesseract_config)
    
        """List of states"""
        self.states = indian_states_cities
        
    """func: extract passport number"""
    def extract_passport_number(self):
        try:
            result = {
                "Passport Number": "",
                "coordinates": []
            }
            passport_number = ""
            matching_line_index_top = None
            matching_line_index_bottom = None
            matching_passport_text = None
            matching_text_regex = r"passport"
            matching_passport_number_coords_top = []
            matching_passport_number_coords_bottom = []

            """find matching text index"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if re.search(matching_text_regex, text.lower(), flags=re.IGNORECASE):
                    matching_line_index_top = i
                    break
            if matching_line_index_top is None:
                return result
        
            """get the top passport number coordinates"""
            for i in range(matching_line_index_top, len(self.coordinates)):
                text = self.coordinates[i][4]
                if len(text) == 8 and text.isupper() and text.isalnum():
                    matching_passport_number_coords_top = [self.coordinates[i][0], self.coordinates[i][1],
                                         self.coordinates[i][2], self.coordinates[i][3]]
                    matching_line_index_bottom = i
                    matching_passport_text = text
                    passport_number = text
                    break
            if matching_line_index_bottom is None:
                return result
                
            """get the bottom passport number coordinates"""
            for i in range(matching_line_index_bottom + 1, len(self.coordinates)):
                text = self.coordinates[i][4]
                if matching_passport_text in text:
                    matching_passport_number_coords_bottom = [self.coordinates[i][0], self.coordinates[i][1],
                                         self.coordinates[i][2], self.coordinates[i][3]]
                    break
            if matching_passport_number_coords_bottom:
                result = {
                    "Passport Number": passport_number,
                    "coordinates": [matching_passport_number_coords_top, matching_passport_number_coords_bottom]
                }
            else:
                result = {
                    "Passport Number": passport_number,
                    "coordinates": [matching_passport_number_coords_top]
                }
            return result
        except Exception as error:
            result = {
                "Passport Number": "",
                "coordinates": []
            }
            return result

    
    """func: extract dates"""
    def extract_dates(self):
        try:
            result = {
                "Passport Dates": "",
                "coordinates": []
                }
            date_text = ""
            date_coords = []
            date_coordinates = []

            """date pattern"""
            date_pattern = r'\d{2}/\d{2}/\d{4}'

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
                "Dates": date_text,
                "coordinates": date_coordinates
            }
            return result
        except Exception as error:
            result = {
                "Passport Dates": "",
                "coordinates": []
            }
            return result


    """func: extract gender"""
    def extract_gender(self):
        try:
            result = {
                "Passport Gender": "",
                "coordinates": []
            }
            gender_text = ""
            matching_text_keyword = ['M', 'F']
            gender_coordinates = []

            """get the coordinates"""
            for i, (x1,y1,x2,y2,text) in enumerate(self.coordinates):
                if text in matching_text_keyword:
                    gender_coordinates = [x1, y1, x2, y2]
                    gender_text = text
                    break
            if not gender_coordinates:
                return result
        
            result = {
                "Passport Gender": gender_text,
                "coordinates": [gender_coordinates]
            }
            return result
        except Exception as error:
            result = {
                "Passport Gender": "",
                "coordinates": []
            }
            return result


    """func: extract surname"""
    def extract_surname(self):
        try:
            result = {
                "Passport Surname": "",
                "coordinates": []
            }
            surname_text = ""
            surname_coords = []
            surname_coordinates = []
            matching_text = "Surname"

            """clean text"""
            clean_text = [i for i in self.text_data.split("\n") if len(i) != 0]

            """find the line that matches search text"""
            matching_text_index = self.__find_matching_line_index(clean_text, matching_text)
            if matching_text_index == 0:
                return result
        
            """get the next line in the text"""
            next_line_list = []
            for line in clean_text[matching_text_index + 2 :]:
                if line.lower() in 'faa ora arr /given names':
                    break
                else:
                    next_line_list.append(line)
            if not next_line_list:
                return result
        
            """get the coordinates"""
            for i in next_line_list:
                for k, (x1, y1, x2, y2, text) in enumerate(self.coordinates):
                    if i == text:
                        surname_coords.append([x1, y1, x2, y2])
                        surname_text = text
        
            for i in surname_coords:
                width = i[2] - i[0]
                surname_coordinates.append([i[0], i[1], i[0] + int(0.40 * width), i[3]])
        
            result = {
                "Passport Surname": surname_text,
                "coordinates": surname_coordinates
            }

            return result
        except Exception as error:
            result = {
                "Passport Surname": "",
                "coordinates": []
            }
            return result

    
    """func: extract given name"""
    def extract_given_name(self):
        try:
            result = {
                "Passport Given Name": "",
                "coordinates": []
            }
            given_name_text = ""
            given_name_cords = []
            given_name_coordinates = []
            matching_text = 'Names'

            """split clean text"""
            clean_text = [i for i in self.text_data.splitlines() if len(i) != 0]

            """find the line that matches the text"""
            matching_line_index = self.__find_matching_line_index(clean_text, matching_text)
            if matching_line_index == 0:
                return result
        
            """get the next line in the text"""
            next_line_list = []
            for line in clean_text[matching_line_index + 1 :]:
                if line.lower() in 'fier /sex':
                    break
                else:
                    next_line_list.append(line)

            if not next_line_list:
                return result
        
            """get the coordinates"""
            for i in next_line_list:
                for k, (x1, y1, x2, y2, text) in enumerate(self.coordinates):
                    if i == text:
                        given_name_cords.append([x1, y1, x2, y2])
                        given_name_text += " "+text
        
            for i in given_name_cords:
                width = i[2] - i[0]
                given_name_coordinates.append([i[0], i[1], i[0] + int(0.40 * width), i[3]])
        
            result = {
                "Passport Given Name": given_name_text,
                "coordinates": given_name_coordinates
            }

            return result
        except Exception as error:
            result = {
                "Passport Given Name": "",
                "coordinates": []
            }
            return result


    """func: extract father name"""
    def extract_father_name(self):
        try:
            result = {
                "Passport Father Name": "",
                "coordinates": []
            }
            father_name_text = ""
            matching_text = "Father"
            father_name_coords = []
            father_name_coordinates = []

            """split clean text"""
            clean_text = [i for i in self.text_data.splitlines() if len(i) != 0]

            """find the line that matches the text"""
            matching_line_index = self.__find_matching_line_index(clean_text, matching_text)
            if matching_line_index == 0:
                return result
        
            """get the next line in the text"""
            next_line_list = []
            for line in clean_text[matching_line_index + 1 :]:
                if "mother" in line.lower():
                    break
                else:
                    next_line_list.extend(line.split())
            if not next_line_list:
                return result
        
            """get the coordinates"""
            if len(next_line_list) > 1:
                next_line_list = next_line_list[:-1]

            for i in next_line_list:
                for k, (x1, y1, x2, y2, text) in enumerate(self.coordinates):
                    if i == text:
                        father_name_coords.append([x1, y1, x2, y2])
                        father_name_text += " "+text
                    if len(next_line_list) == len(father_name_coords):
                        break
        
            for i in father_name_coords:
                width = i[2] - i[0]
                father_name_coordinates.append([i[0], i[1], i[0] + int(0.40 * width), i[3]])
        
            result = {
                "Passport Father Name": father_name_text,
                "coordinates": father_name_coordinates
            }
            return result
        except Exception as error:
            result = {
                "Passport Father Name": "",
                "coordinates": []
            }
            return result


    """func: extract mother name"""
    def extract_mother_name(self):
        try:
            result = {
                "Passport Mother Name": "",
                "coordinates": []
            }
            matching_text = "Mother"
            mother_coords = []
            mother_text = ""
            mother_coordinates = []

            """split clean text"""
            clean_text = [i for i in self.text_data.splitlines() if len(i) != 0]

            # find the line that matches search text
            matching_line_index = self.__find_matching_line_index(clean_text, matching_text)
            if matching_line_index == 0:
                return result
        
            """get the next line in the text"""
            next_line_list = []
            for line in clean_text[matching_line_index + 1 :]:
                if "af ar of a ora /name of spouse" in line.lower():
                    break
                else:
                    next_line_list.extend(line.split())
            if not next_line_list:
                return result
        
            """get the coordinates"""
            if len(next_line_list) > 1:
                next_line_list = next_line_list[:-1]

            for i in next_line_list:
                for k, (x1, y1, x2, y2, text) in enumerate(self.coordinates):
                    if i == text:
                        mother_coords.append([x1, y1, x2, y2])
                        mother_text += " "+text
                    if len(next_line_list) == len(mother_coords):
                        break
        
            for i in mother_coords:
                width = i[2] - i[0]
                mother_coordinates.append([i[0], i[1], i[0] + int(0.40 * width), i[3]])
        
            result = {
                "Passport Mother Name": mother_text,
                "coordinates": mother_coordinates
            }
            return result
        except Exception as error:
            result = {
                "Passport Mother Name": "",
                "coordinates": []
            }
            return result

    
    """func: extract ind-name"""
    def extract_ind_name(self):
        try:
            result = {
                "Passport IND Name": "",
                "coordinates": []
            }
            ind_name_text = ""
            ind_name_cords = []
            ind_name_coordinates = []

            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if "IND" in text and '<' in text:
                    ind_name_cords.append([x1, y1, x2, y2])
                    ind_name_text += " "+text
                    break
            if not ind_name_cords:
                return result
            if len(ind_name_cords) > 1:
                ind_name_cords = ind_name_cords[:-1]

            for i in ind_name_cords:
                width = i[2] - i[0]
                ind_name_coordinates.append([i[0], i[1], i[0] + int(0.40 * width), i[3]])
        
            result = {
                "Passport IND Name": ind_name_text,
                "coordinates": ind_name_coordinates
            }
            return result
        except Exception as error:
            result = {
                "Passport IND Name": "",
                "coordinates": []
            }
            return result


    """func: extract pincode"""
    def extract_pincode(self):
        try:
            result = {
                "Passport Pincode": "",
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
        
            if not pincode_coordinates:
                return result
            
            for i in pincode_coords:
                width = i[2] - i[0]
                pincode_coordinates.append([i[0], i[1], i[0] + int(0.30 * width), i[3]])
        
            result = {
                "Passport Pincode": pincode_number,
                "coordinates": pincode_coordinates
            }
            return result
        except Exception as error:
            result = {
                "Passport Pincode": "",
                "coordinates": []
            }
            return result

    
    """func: extract state"""
    def extract_state(self):
        try:
            result = {
                "Passport Place": "",
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
                "Passport Place": state_name,
                "coordinates": state_coordinates
            }

            return result
        except Exception as error:
            result = {
                "Passport Place": "",
                "coordinates": []
            }
            return result

    
    def __find_matching_line_index(self, lines: list, matching_text: str ) -> int:
        # find the line that matches search text
        for i,line in enumerate(lines):
            if matching_text in line:
                return i
        return 0

    """func: collect passport info"""
    def collect_passport_info(self) -> dict:
        passport_doc_info_list = []

        """Check Document mode"""
        if self.DOCUMENT_MODE == 1:

            """Collect: Passport Number"""
            passport_number = self.extract_passport_number()
            if len(passport_number['coordinates']) != 0:
                passport_doc_info_list.append(passport_number)
            else:
                passport_doc_info_list.append(passport_number)
                self.logger.error("| Passport number not found")
            
            """Collect: Dates"""
            passport_dates = self.extract_dates()
            if len(passport_dates['coordinates']) != 0:
                passport_doc_info_list.append(passport_dates)
            else:
                passport_doc_info_list.append(passport_dates)
                self.logger.error("| Passport dates not found")
            
            """Collect: Gender"""
            gender = self.extract_gender()
            if len(gender['coordinates']) != 0:
                passport_doc_info_list.append(gender)
            else:
                passport_doc_info_list.append(gender)
                self.logger.error("| Passport gender not found")
            
            """Collect: Surname"""
            surname = self.extract_surname()
            if len(surname['coordinates']) != 0:
                passport_doc_info_list.append(surname)
            else:
                passport_doc_info_list.append(surname)
                self.logger.error("| Passport surname not found")
            
            """Collect: Given name"""
            given_name = self.extract_given_name()
            if len(given_name['coordinates']) != 0:
                passport_doc_info_list.append(given_name)
            else:
                passport_doc_info_list.append(given_name)
                self.logger.error("| Passport given name not found")
            
            """Collect: Father's name"""
            father_name = self.extract_father_name()
            if len(father_name['coordinates']) != 0:
                passport_doc_info_list.append(father_name)
            else:
                passport_doc_info_list.append(father_name)
                self.logger.error("| Passport father's name not found")
            
            """Collect: Mother's name"""
            mother_name = self.extract_mother_name()
            if len(mother_name['coordinates']) != 0:
                passport_doc_info_list.append(mother_name)
            else:
                passport_doc_info_list.append(mother_name)
                self.logger.error("| Passport mother name not found")
            
            """Collect: IND name"""
            ind_name = self.extract_ind_name()
            if len(ind_name['coordinates']) != 0:
                passport_doc_info_list.append(ind_name)
            else:
                passport_doc_info_list.append(ind_name)
                self.logger.error("| Passport IND name not found")
            
            """Collect: Pincode"""
            pincode_number = self.extract_pincode()
            if len(pincode_number['coordinates']) != 0:
                passport_doc_info_list.append(pincode_number)
            else:
                passport_doc_info_list.append(pincode_number)
                self.logger.error("| Passport Pincode number not found")
            
            """Collect: State"""
            state = self.extract_state()
            if len(state['coordinates']) != 0 :
                passport_doc_info_list.append(state)
            else:
                passport_doc_info_list.append(state)
                self.logger.error("| Passport State name not found")
            
            """check passport_doc_info_list"""
            all_keys_and_coordinates_empty =  all(all(not v for v in d.values()) for d in passport_doc_info_list)
            if all_keys_and_coordinates_empty:
                return {"message": "Unable to extract Passport information", "status": "REJECTED"}
            else:
                return {"message": "Successfully Redacted Passport Document", "status": "REDACTED", "data": passport_doc_info_list}

        else:

            """Collect: Passport Number"""
            passport_number = self.extract_passport_number()
            if len(passport_number['coordinates']) == 0:
                self.logger.error("| Passport number not found")
                return {"message": "Unable to extract passport number", "status": "REJECTED"}
            passport_doc_info_list.append(passport_number)
 
            """Collect: Dates"""
            passport_dates = self.extract_dates()
            if len(passport_dates['coordinates']) == 0:
                self.logger.error("| Passport dates not found")
                return {"message": "Unable to extract dates from passport document", "status": "REJECTED"}
            passport_doc_info_list.append(passport_dates)
        
            """Collect: Gender"""
            gender = self.extract_gender()
            if len(gender['coordinates']) == 0:
                self.logger.error("| Passport gender not found")
                return {"message": "Unable to extract gender from passport", "status": "REJECTED"}
            passport_doc_info_list.append(gender)

            """Collect: Surname"""
            surname = self.extract_surname()
            if len(surname['coordinates']) == 0:
                self.logger.error("| Passport surname not found")
                return {"message": "Unable to extract surname from passport document", "status": "REJECTED"}
            passport_doc_info_list.append(surname)

            """Collect: Given name"""
            given_name = self.extract_given_name()
            if len(given_name["coordinates"]) == 0:
                self.logger.error("| Passport given name not found")
                return {"message": "Unable to extract given name from passport", "status": "REJECTED"}
            passport_doc_info_list.append(given_name)

            """Collect: Father's name"""
            father_name = self.extract_father_name()
            if len(father_name["coordinates"]) == 0:
                self.logger.error("| Passport father's name not found")
                return {"message": "Unable to extract father's name from passport", "status": "REJECTED"}
            passport_doc_info_list.append(father_name)

            """Collect: Mother's name"""
            mother_name = self.extract_mother_name()
            if len(mother_name["coordinates"]) == 0:
                self.logger.error("| Passport mother name not found")
                return {"message": "Unable to extract mother name", "status": "REJECTED"}
            passport_doc_info_list.append(mother_name)

            """Collect: IND name"""
            ind_name = self.extract_ind_name()
            if len(ind_name["coordinates"]) == 0:
                self.logger.error("| Passport IND name not found")
                return {"message": "Unable to extract IND name from Passport", "status": "REJECTED"}
            passport_doc_info_list.append(ind_name)

            """Collect: Pincode"""
            pincode_number = self.extract_pincode()
            if len(pincode_number['coordinates']) == 0:
                self.logger.error("| Passport Pincode not found")
                return {"message": "Unable to extract Pincode from Passport", "status": "REJECTED"}
            passport_doc_info_list.append(pincode_number)

            """Collect: State"""
            state = self.extract_state()
            if len(state['coordinates']) == 0:
                self.logger.error("| Passport Place name not found")
                return {"message": "Unable to extract Place name from Passport", "status": "REJECTED"}
            passport_doc_info_list.append(state)

            return {"message": "Successfully Redacted Passport Document", "status": "REDACTED", "data": passport_doc_info_list}
