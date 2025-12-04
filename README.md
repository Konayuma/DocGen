# DocGen: AI-Powered Document Generator

Generate professional documents using the Google Gemini API. Upload PDFs, Word docs, text files, or images, provide a prompt, and let AI create new content for you.

## Features

- 📄 **Multi-format Support**: PDF, DOCX, TXT, PNG, JPG, TIFF, BMP
- 🤖 **Powered by Gemini API**: Access to Google's latest AI models
- ⚡ **Fast Processing**: Real-time text extraction and generation
- 🎨 **Beautiful UI**: Bootstrap 5 responsive interface
- 📥 **Easy Downloads**: Generated PDFs ready to use
- 🔒 **Secure**: Environment variable API key storage

## Quick Start

### Prerequisites
- Python 3.11+
- Tesseract OCR installed (for image/scanned PDF support)
- Google Gemini API key

### Installation

1. **Clone/setup project**:
   ```powershell
   cd c:\Users\Sepo Konayuma\DocGen
   ```

2. **Create virtual environment**:
   ```powershell
   python -m venv venv
   .\.venv\Scripts\Activate
   ```

3. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Install Tesseract OCR** (optional, for image extraction):
   - Download from: https://github.com/UB-Mannheim/tesseract/wiki
   - Or use Chocolatey: `choco install tesseract`

5. **Setup environment variables**:
   ```powershell
   copy .env.example .env
   ```
   - Edit `.env` and add your Gemini API key:
   ```
   GEMINI_API_KEY=your-actual-key-here
   ```

6. **Run the application**:
   ```powershell
   uvicorn docgen.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Open in browser**:
   - Navigate to: `http://localhost:8000`

## Usage

1. **Upload**: Drag & drop or select documents (PDF, DOCX, TXT, images)
2. **Prompt**: Enter instructions (summarize, rewrite, extract, etc.)
3. **Generate**: Click "Generate Document" and wait for processing
4. **Download**: Once complete, download your generated PDF

## API Endpoints

### Core Endpoints

**POST /upload** - Upload documents for text extraction
- Request: `multipart/form-data` with `files` field
- Response: `{ upload_id, files[], total_chars }`

**POST /generate** - Start document generation job
- Request: `{ upload_id, prompt, model?, temperature?, max_tokens? }`
- Response: `{ job_id, upload_id, status, timestamp }`

**GET /status/{job_id}** - Check generation status
- Response: `{ job_id, status, progress, error?, completion_time? }`

**GET /download/{job_id}** - Download generated PDF
- Response: PDF file (application/pdf)

### Info Endpoints

**GET /health** - Health check
**GET /api/info** - API information (models, formats, limits)
**GET /** - Main UI page

## Project Structure

```
docgen/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration & environment loading
├── utils.py             # Utility functions
├── models/
│   ├── __init__.py
│   └── schemas.py       # Pydantic request/response models
├── routers/
│   ├── __init__.py
│   └── document.py      # API endpoints (/upload, /generate, etc.)
├── services/
│   ├── __init__.py
│   ├── extraction.py    # Text extraction from various formats
│   ├── gemini_client.py # Gemini API wrapper
│   └── pdf_generator.py # ReportLab PDF generation
├── templates/
│   └── index.html       # Bootstrap frontend
└── static/              # CSS, JS assets
tests/
├── test_extraction.py   # Unit tests for text extraction
├── test_generation.py   # Unit tests for PDF generation
└── test_api.py          # Integration tests
```

## Configuration

Edit `.env` file to customize:

```env
GEMINI_API_KEY=your-key-here          # Required: Gemini API key
GEMINI_MODEL=gemini-2.5-flash         # Model to use
MAX_FILE_SIZE_MB=50                   # Max upload file size
DEBUG=False                           # Debug mode
TEMP_DIR=./temp                       # Temporary files directory
UPLOAD_RETENTION_SECONDS=3600         # How long to keep uploads
JOB_RETENTION_SECONDS=86400           # How long to keep jobs
```

## Supported Formats

| Format | Extension | Method | Accuracy |
|--------|-----------|--------|----------|
| PDF (native text) | .pdf | PyMuPDF | High |
| PDF (scanned) | .pdf | OCR (Tesseract) | Medium-High |
| Word Document | .docx | python-docx | High |
| Plain Text | .txt | Native | Perfect |
| Image (PNG, JPG) | .png, .jpg | OCR (Tesseract) | Medium |
| Bitmap | .bmp | OCR (Tesseract) | Medium |
| TIFF | .tiff | OCR (Tesseract) | Medium-High |

## Gemini Models

### Recommended Models

**gemini-2.5-flash** (Default)
- Best price-performance ratio
- 1M token context window
- Free tier: 10 requests/min, 250K tokens/min

**gemini-2.5-pro**
- Advanced reasoning and analysis
- Ideal for complex document processing
- Free tier: 2 requests/min

**gemini-2.5-flash-lite**
- Fastest and cheapest
- Good for high-volume tasks
- Free tier: 15 requests/min

## Cost Estimates

With Gemini API (as of Dec 2024):
- Input: $0.075 per 1M tokens
- Output: $0.30 per 1M tokens
- Typical 10-page document: ~40K tokens input, 5K tokens output ≈ $0.002

## Deployment

### Docker

Build and run with Docker:

```powershell
docker build -t docgen .
docker run -p 8000:8000 -e GEMINI_API_KEY=your-key-here docgen
```

### Production with Gunicorn

```powershell
pip install gunicorn
gunicorn docgen.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Environment Variables (Production)

Set via system or container:
```powershell
$env:GEMINI_API_KEY='your-key'
$env:DEBUG='False'
$env:MAX_FILE_SIZE_MB='100'
```

## Security Considerations

1. **API Key**: Store in environment variables, never hardcode
2. **File Uploads**: Validated by extension and MIME type, size limited
3. **Temp Files**: Automatically cleaned up after retention period
4. **PII**: Be cautious with sensitive documents; check Gemini data usage policies
5. **Rate Limiting**: Use slowapi for production rate limiting

## Troubleshooting

### Tesseract Not Found
```powershell
# Windows: Install via Chocolatey
choco install tesseract

# Or download: https://github.com/UB-Mannheim/tesseract/wiki
```

### API Key Error
```
ValueError: GEMINI_API_KEY environment variable not set
```
Solution: Check `.env` file and ensure `GEMINI_API_KEY` is set with a valid key.

### PDF Extraction Fails
- Ensure file is not corrupted
- Try uploading as image if scanned PDF
- Check temp directory has write permissions

### Generation Takes Too Long
- Current model is busy; try reducing document size
- Consider using `gemini-2.5-flash-lite` for faster responses
- Check internet connection

## Testing

Run tests with pytest:

```powershell
pip install pytest pytest-asyncio
pytest tests/ -v
```

### Test Files
- `test_extraction.py`: Text extraction from all formats
- `test_generation.py`: PDF generation with various content
- `test_api.py`: Full end-to-end API tests

## Contributing

Contributions welcome! Areas for enhancement:
- Background job queue (Celery+Redis)
- User authentication & database
- Multiple output formats (DOCX, HTML)
- Streaming Gemini responses
- Custom PDF templates
- Batch document processing

## License

MIT License - feel free to use for personal and commercial projects.

## Support

- Issues: Check GitHub issues
- Docs: https://ai.google.dev/gemini-api/docs
- API Reference: https://fastapi.tiangolo.com/

---

Built with ❤️ using FastAPI, ReportLab, and Google Gemini API
