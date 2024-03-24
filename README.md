# OCR for KYC Documents

This Python project is designed for Optical Character Recognition (OCR) on KYC (Know Your Customer) documents. The primary objective is to extract text from these documents and obtain their coordinates for redaction purposes.

## Features

- Extracts text content from KYC documents.
- Provides coordinates of the extracted text for redaction.
- Utilizes OCR technology for accurate text recognition.

## Getting Started

### Prerequisites

- Python 3.x
- Tesseract-OCR 5.x

### Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/Devopcasting/KYC-OCRR.git
    cd KYC-OCRR
    ```

2. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

### Usage

1. Configure your project settings in `config.ini`:

    ```ini
    [Paths]
    upload = /path/to/upload/folder
    workspace = /path/to/workspace/folder
    ```

2. Run the OCR for KYC documents:

    ```bash
    python ocrr_engine.py
    ```

3. View the extracted text and coordinates for redaction.

## Configuration

Adjust the project settings in `config.ini` to match your specific file paths and requirements.