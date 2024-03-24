import re

class IdentifyPassport:
    def __init__(self, clean_text: list) -> None:
        self.clean_text = clean_text
        # Regular expression pattern for Passport identifiers
        self.passport_regex = r"\b(?:republic|jpassport|passport)\b"

    def check_passport(self) -> bool:
        for text in self.clean_text:
            if re.search(self.passport_regex, text, flags=re.IGNORECASE):
                return True
        return False