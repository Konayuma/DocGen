"""
Basic tests for document extraction functionality.
"""
import pytest
import os
import tempfile
from docgen.services.extraction import TextExtractor


@pytest.mark.asyncio
async def test_txt_extraction():
    """Test plain text file extraction."""
    content = "Hello, this is a test document.\nWith multiple lines.\nAnd more content."
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        f.flush()
        
        text, metadata = TextExtractor.extract(f.name)
        
        assert "Hello" in text
        assert metadata["extraction_method"] == "txt_native"
        assert metadata["chars"] > 0
        
        os.unlink(f.name)


def test_invalid_extension():
    """Test handling of unsupported file types."""
    with pytest.raises(ValueError):
        TextExtractor.extract("file.xyz")
