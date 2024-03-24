import pytesseract
from pancard.identify_pancard import IdentifyPanCard
from aadhaarcard.identify_aadhaarcard import IdentifyAadhaarCard
from passport.identify_passport import IdentifyPassport
from drivingl.identify_dl import IdentifyDrivingLicense
from cdsl.identify_cdsl import IdentifyCDSL
from e_pancard.identify_e_pancard import IdentifyEPanCard
from check_img_rgb.image_rgb import CheckImageRGB
from helper.clean_text import CleanText

class DocumentTypeIdentification:
    def __init__(self, document_path: str) -> None:

        self.document_path = document_path
    
        """Clean the extracted text"""
        data_text = self.get_text_from_image()
        clean_text_data = CleanText(data_text).clean_text()
        
        """Initialize doocument objects"""
        self.document_identification_objects = {
            "CDSL": IdentifyCDSL(clean_text_data).check_cdsl(),
            "E-PAN": IdentifyEPanCard(clean_text_data).check_e_pan_card(),
            "PAN": IdentifyPanCard(clean_text_data).check_pan_card(),
            "Aadhaar Format": IdentifyAadhaarCard(clean_text_data).check_aadhaar_card_format(),
            "E-Aadhaar": IdentifyAadhaarCard(clean_text_data).check_e_aadhaar_card(),
            "Aadhaar": IdentifyAadhaarCard(clean_text_data).check_aadhaarcard(),
            "Bharat Passport": IdentifyPassport(clean_text_data).check_passport(),
            "Bharat DL": IdentifyDrivingLicense(clean_text_data).check_dl()
        }
    
    def get_text_from_image(self) -> str:
        if CheckImageRGB(self.document_path).check_rgb_image():
            tesseract_config = r'-l eng --oem 3'
        else:
            tesseract_config = r'-l eng --oem 3 --psm 11'
        
        return pytesseract.image_to_string(self.document_path, output_type=pytesseract.Output.DICT, config=tesseract_config)

    def identify_document(self, document_type: str) -> bool:
        if document_type in self.document_identification_objects:
            return self.document_identification_objects[document_type]
        else:
            return False