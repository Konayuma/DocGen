"""
Tests for PDF generation functionality.
"""
import pytest
from docgen.services.pdf_generator import PDFGenerator


def test_pdf_generation():
    """Test basic PDF generation."""
    content = "This is a test document.\n\nWith multiple paragraphs.\n\nFor testing purposes."
    
    pdf_bytes = PDFGenerator.generate_pdf(
        content=content,
        title="Test Document",
        author="Test Author",
    )
    
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b'%PDF')  # PDF magic number


def test_sanitize_text():
    """Test text sanitization for PDF generation."""
    unsafe = "<script>alert('xss')</script>"
    safe = PDFGenerator.sanitize_text(unsafe)
    
    assert "<script>" not in safe
    assert "&lt;script&gt;" in safe
