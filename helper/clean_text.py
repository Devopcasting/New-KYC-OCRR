import re

class CleanText:
    def __init__(self, text: str) -> None:
        self.text = text
    
    # func: clean text
    def clean_text(self) -> list:
        clean_data_re = re.sub(r'[^a-zA-Z0-9\s:/-]',' ', self.text["text"])
        clean_data = []
        for data in clean_data_re.split('\n'):
            left_strip = data.lstrip()
            right_strip = left_strip.rstrip()
            if len(right_strip) != 0:
                clean_data.append(right_strip)
        return clean_data