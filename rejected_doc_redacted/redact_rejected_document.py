import numpy as np
import cv2

class RedactRejectedDocument:
    def __init__(self, document_path) -> None:
        self.document_path = document_path
    
    """Get 75% document coordinates"""
    def rejected(self) -> list:
        # Read the image
        image = cv2.imread(self.document_path)
        # Get the image height and width
        height, width = image.shape[:2]
        # Calculate the coordinates of the 75% of the image
        x1 = 0
        y1 = 0
        x2 = width
        y2 = int(height * 0.890)
        coordinates_list = []
        coordinates_list.append([x1, y1, x2, y2])
        return coordinates_list