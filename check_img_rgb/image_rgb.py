import cv2

class CheckImageRGB:
    def __init__(self, docuement_path: str) -> None:
        self.document_path = docuement_path
    
    def check_rgb_image(self) -> bool:
        document = cv2.imread(self.document_path)
        if len(document.shape) < 3: return True
        if document.shape[2]  == 1: return True
        b,g,r = document[:,:,0], document[:,:,1], document[:,:,2]
        if (b==g).all() and (b==r).all(): return True
        return False
