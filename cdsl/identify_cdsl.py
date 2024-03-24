import re

class IdentifyCDSL:
    def __init__(self, clean_text: list) -> None:
        self.clean_text = clean_text
        # Regular expression pattern for CDSL identifiers
        self.cdsl_regex = r"\b(?: cdsl|ventures|limited|kyc)\b"

    def check_cdsl(self) -> bool:
        for text in self.clean_text:
            if re.search(self.cdsl_regex, text, flags=re.IGNORECASE):
                return True
        return False