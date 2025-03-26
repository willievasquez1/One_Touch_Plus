"""PDF text extraction utilities, with optional OCR support.

This module provides functionality to extract text content from PDF files.
If the PDF is scanned (images only), it can use OCR (Optical Character Recognition) as a fallback.
"""

def extract_text_from_pdf(file_path, config):
    """Extract text from a PDF file.

    If OCR is enabled in the configuration and the PDF has non-text content, 
    this function will attempt to perform OCR on each page.

    Args:
        file_path (str): Path to the PDF file to extract text from.
        config (dict): Scraper configuration, which may include PDF handling settings (e.g., ocr_enabled).

    Returns:
        str: The extracted text content from the PDF.
    """
    text_content = ""
    # TODO: Implement text extraction using PyMuPDF or PyPDF2 for text PDFs.
    # If the PDF contains images (scanned), and config['pdf'].get('ocr_enabled'):
    #    Use pytesseract (OCR) on images (perhaps using pdf2image to get images from PDF).
    # Example:
    # import fitz  # PyMuPDF
    # doc = fitz.open(file_path)
    # for page in doc:
    #     text_content += page.get_text()
    # if not text_content and config.get('pdf', {}).get('ocr_enabled'):
    #     # use OCR on page images
    #     text_content = ocr_extract_from_pdf(file_path)
    return text_content
