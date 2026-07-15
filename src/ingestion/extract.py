"""
PDF text extraction for CBE circulars.

Handles bilingual (Arabic/English) PDFs. Arabic text extracted via PyMuPDF
often comes out visually reordered — this module is responsible for getting
clean, correctly-ordered text out before chunking.
"""


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract raw text from a single PDF file."""
    raise NotImplementedError


def clean_text(raw_text: str) -> str:
    """Strip repeated headers/footers, page numbers, boilerplate."""
    raise NotImplementedError
