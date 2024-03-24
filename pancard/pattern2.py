import re

class PanCardPattern2:
    def __init__(self,  coordinates, text, index_num) -> None:
        self.coordinates = coordinates
        self.text = text
        self.index_num = index_num
        if self.index_num == 1:
            self.LABEL_NAME = "Pancard Username"
        else:
            self.LABEL_NAME = "Pancard Father's Name"

    """func: extract username"""
    def extract_username_p2(self):
        try:
            result = {
                f"{self.LABEL_NAME}": "",
                "coordinates": []
            }
            matching_text_coords = []
            next_line_list = ''

            matching_text_keyword = ['OF INDIA', "GOVT. OF INDIA"," GOVT.", "INDIA", "INCOME", "TAX", "DEPARTMENT", "DEPARTNENT", "INCOME TAX DEPARTNENT"]

            """split the text into lines"""
            lines = [i for i in self.text.splitlines() if len(i) != 0]
        
            """find the matching text index"""
            matching_text_index = self.__find_matching_text_index_username(lines, matching_text_keyword)
    
            if matching_text_index == 404:
                return result
        
            """get the next line of matching index"""
            pattern = r"\b(?:department|departnent|income|sires|account|card|tax|govt|are|an|ad|z|of india)\b(?=\s|\W|$)|[-=\d]+"
            for line in lines[matching_text_index:]:
                match = re.search(pattern, line.lower(), flags=re.IGNORECASE)
                if match:
                    continue
                if line.isupper():
                    next_line_list = line.split()
                    break
        
            if not next_line_list:
                return result
        
            """remove special characters and white spaces"""
            clean_next_line = [element for element in next_line_list if re.search(r'[a-zA-Z0-9]', element)]
            user_name = " ".join(clean_next_line)
            if len(clean_next_line) > 1:
                clean_next_line = clean_next_line[:-1]
        
            """get the coordinates"""
            for i,(x1,y1,x2,y2,text) in enumerate(self.coordinates):
                if text in clean_next_line:
                    matching_text_coords.append([x1, y1, x2, y2])
                if len(matching_text_coords) == len(clean_next_line):
                    break
    
            if len(matching_text_coords) > 1:
                result = {
                    f"{self.LABEL_NAME}": user_name,
                    "coordinates": [[matching_text_coords[0][0], matching_text_coords[0][1], matching_text_coords[-1][2], matching_text_coords[-1][3]]]
                }
            else:
                result = {
                    f"{self.LABEL_NAME}": user_name,
                    "coordinates": [[matching_text_coords[0][0], matching_text_coords[0][1], matching_text_coords[0][2], matching_text_coords[0][3]]]
                }

            return result
        except Exception as error:
            result = {
                f"{self.LABEL_NAME}": "",
                "coordinates": []
            }
            return result


    def __find_matching_text_index_username(self, lines: list, matching_text: list) -> int:
        for i,line in enumerate(lines):
            for k in matching_text:
                if k in line:
                    return i
        return 404

    """func: extract father's name"""
    def extract_fathername_p2(self):
        try:
            result = {
                f"{self.LABEL_NAME}": "",
                "coordinates": []
            }
            matching_text = None
            matching_text_list = None
            matching_index = None
            matching_text_coords = []

            """split the text into lines"""
            lines = [i for i in self.text.splitlines() if len(i) != 0]

            """reverse line list"""
            reverse_line = lines[::-1]

            """Data patterns: DD/MM/YYY, DD-MM-YYY"""
            date_pattern = r'\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}'
            matching_pattern = r"bonn|birth"
            for i, text in enumerate(reverse_line):
                match_dob = re.search(date_pattern, text)
                match_pattern = re.search(matching_pattern, text, flags=re.IGNORECASE)
                if match_dob or match_pattern:
                    if len(reverse_line[i + 1]) == 1:
                        matching_index = i + 2
                        break
                    else:
                        matching_index = i + 1
                        break
        
            if not matching_index:
                return result
        
            for text in reverse_line[matching_index :]:
                if text.isupper():
                    matching_text = text
                    matching_text_list = text.split()
                    break
        
            if not matching_text_list:
                return result
        
            if len(matching_text_list) > 1:
                matching_text_list = matching_text_list[:-1]

            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if text in matching_text_list:
                    matching_text_coords.append([x1, y1, x2, y2])
                if len(matching_text_list) == len(matching_text_coords):
                    break
        
            if len(matching_text_coords) > 1:
                result = {
                    f"{self.LABEL_NAME}": matching_text,
                    "coordinates": [[matching_text_coords[0][0], matching_text_coords[0][1], matching_text_coords[-1][2], matching_text_coords[-1][3]]]
                }
            else:
                result = {
                    f"{self.LABEL_NAME}": matching_text,
                    "coordinates": [[matching_text_coords[0][0], matching_text_coords[0][1], matching_text_coords[0][2], matching_text_coords[0][3]]]
                }
            return result
        except Exception as error:
            result = {
                f"{self.LABEL_NAME}": "",
                "coordinates": []
            }
            return result
        
    def __find_matching_text_index_father_name(self, lines, matching_text) -> int:
        for i,line in enumerate(lines):
            if len(line) != 1 and line == matching_text:
                if len(lines[i -1]) != 1:
                    return i -1
                return i - 2
        return 404