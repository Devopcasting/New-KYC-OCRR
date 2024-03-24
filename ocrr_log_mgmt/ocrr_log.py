import logging
import configparser
import os

class OCRREngineLogging:
    def __init__(self, log_file='ocrr.log', log_level=logging.INFO) -> None:
        # create a ConfigParser object with the allow_no_value keyword argument
        config = configparser.ConfigParser(allow_no_value=True)
        # read config.ini
        config.read(r'C:\Program Files (x86)\OCRR\config\config.ini')
        occr_log_path = config['Paths']['logs']

        self.log_file = os.path.join(occr_log_path,log_file)
        self.log_level = log_level
    
    def configure_logger(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(self.log_level)

        # Check if a file handler already exists
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler) and handler.baseFilename == self.log_file:
                return logger
        
        # Create a file handler to write logs to a file
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(self.log_level)

        formatter = logging.Formatter('%(process)d %(asctime)s %(levelname)s %(message)s')
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
     
        return logger