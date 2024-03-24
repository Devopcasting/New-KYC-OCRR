import pytesseract
import re

class EPancardSignatureTextCoordinates:
    def __init__(self, image_path, doc_type=None) -> None:
        self.image_path = image_path
        self.doc_type = doc_type
    
    # func: generate coordinates
    def generate_text_coordinates(self) -> list:
        data = pytesseract.image_to_data(self.image_path, output_type=pytesseract.Output.DICT, lang="hin+eng")
        coordinates = []
        for i in range(len(data['text'])):
            text = data['text'][i]
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            # Filter out empty strings and  special characters
            if text.strip() != '':
                coordinates.append((x,y,x + w, y + h, text))
        return coordinates