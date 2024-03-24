import re

class PanCardPattern1:
    def __init__(self, coordinates, text, matching_text_keyword: list, index_num) -> None:
        self.coordinates = coordinates
        self.text = text
        self.matching_text_keyword = matching_text_keyword
        self.index_num = index_num
        
        if self.index_num == 1:
            self.LABEL_NAME = "Pancard Username"
        else:
            self.LABEL_NAME = "Pancard Father's Name"
    
    """func: extract username"""
    def extract_username_fathername_p1(self):
        try:
            result = {
                f"{self.LABEL_NAME}": "",
                "coordinates": []
            }
            matching_text_coords = []
            next_line_list = ''
    
            """split the text into lines"""
            lines = [i for i in self.text.splitlines() if len(i) != 0]

            """find the matching text index"""
            matching_text_index = self.__find_matching_text_index_username(lines, self.matching_text_keyword)
            if matching_text_index == 404:
                return result
        
            """get the next line of matching index"""
            #next_line_list = lines[matching_text_index + 1].split()
            for text in lines[matching_text_index + 1:]:
                if text.isupper():
                    next_line_list = text.split()
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
        matching_pattern = r"\b(?:" + "|".join(re.escape(word) for word in matching_text) + r")\b"
        for i, line in enumerate(lines):
            if re.search(matching_pattern, line, flags=re.IGNORECASE):
                return i
        return 404