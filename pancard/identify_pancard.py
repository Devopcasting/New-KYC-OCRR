import re

class IdentifyPanCard:
    def __init__(self, clean_text: list) -> None:
        self.clean_text = clean_text
        # Regular expression pattern for PAN card identifiers
        self.pancard_regex = r"\b(?: account|petraancnt|income|tax|incometax|department|permanent|petianent|incometaxdepartment|incombtaxdepartment|pormanent|perenent|tincometaxdepakinent)\b"

    def check_pan_card(self) -> bool:
        for text in self.clean_text:
            if re.search(self.pancard_regex, text, flags=re.IGNORECASE):
                return True
        return False