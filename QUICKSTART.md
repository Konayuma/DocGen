# Quick Start Guide for DocGen

## ⚡ 5-Minute Setup

### Step 0: Install uv (Optional but Recommended)

```powershell
# Using pip
pip install uv

# Or using Chocolatey (faster)
choco install uv
```

### Step 1: Install Dependencies

```powershell
cd C:\Users\Sepo Konayuma\DocGen

# Create virtual environment
uv venv venv

# Activate virtual environment
.\venv\Scripts\Activate

# Install Python packages (10x faster with uv!)
uv pip install -r requirements.txt

# OR if you prefer pip
pip install -r requirements.txt
```

### Step 2: Install Tesseract OCR (Optional but Recommended)

For image and scanned PDF support:

```powershell
# Option A: Using Chocolatey (recommended if installed)
choco install tesseract

# Option B: Manual download
# 1. Visit: https://github.com/UB-Mannheim/tesseract/wiki
# 2. Download the Windows installer
# 3. Run installer, use default C:\Program Files\Tesseract-OCR path
```

### Step 3: Set Up Environment Variables

```powershell
# Copy example config
copy .env.example .env

# Edit .env with your Gemini API key
# Open .env and change:
# GEMINI_API_KEY=your-actual-key-here
```

**Getting your API Key:**
1. Go to: https://aistudio.google.com/apikey
2. Sign in with Google account
3. Click "Create API key"
4. Copy and paste into `.env` file

### Step 4: Run the Application

```powershell
# Make sure virtual environment is still active
uvicorn docgen.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 5: Open in Browser

```
http://localhost:8000
```

## 📋 Usage

1. **Upload**: Drag files or click to upload (PDF, DOCX, TXT, images)
2. **Enter Prompt**: Describe what you want the AI to generate
3. **Generate**: Click the generate button
4. **Download**: Once complete, download your PDF

## 🧪 Run Tests

```powershell
pip install pytest pytest-asyncio

pytest tests/ -v
```

## 📦 Project Files

| File | Purpose |
|------|---------|
| `docgen/main.py` | FastAPI entry point |
| `docgen/config.py` | Configuration loader |
| `docgen/services/extraction.py` | Text extraction logic |
| `docgen/services/gemini_client.py` | Gemini API wrapper |
| `docgen/services/pdf_generator.py` | PDF generation logic |
| `docgen/routers/document.py` | API routes |
| `docgen/templates/index.html` | Frontend UI |
| `requirements.txt` | Python dependencies |
| `.env` | Environment variables (create from .env.example) |

## 🔧 Troubleshooting

### Import Error: "No module named google.genai"
```powershell
pip install google-genai
```

### API Key not found
- Verify `.env` file exists in project root
- Check `GEMINI_API_KEY=` is set correctly
- Restart the application

### Tesseract not found (for image extraction)
```powershell
# Option 1: Install via Chocolatey
choco install tesseract

# Option 2: Add to PATH manually if already installed
# Set-Item -Path env:PATH -Value "$env:PATH;C:\Program Files\Tesseract-OCR"
```

### Port 8000 already in use
```powershell
# Use a different port
uvicorn docgen.main:app --reload --host 0.0.0.0 --port 8001
```

## 🚀 Next Steps

After getting the basic setup running:

1. **Customize PDF Templates** - Edit `PDFGenerator` in `docgen/services/pdf_generator.py`
2. **Add Database** - Replace in-memory storage with SQLAlchemy/PostgreSQL
3. **Deploy** - Use `Dockerfile` for containerization or Heroku/Railway for hosting
4. **Add Authentication** - Implement user login with FastAPI security
5. **Background Jobs** - Use Celery+Redis for long-running generations

## 📚 Documentation

- **FastAPI**: https://fastapi.tiangolo.com/
- **Gemini API**: https://ai.google.dev/gemini-api/docs
- **ReportLab**: https://www.reportlab.com/docs/reportlab-userguide.pdf
- **Bootstrap 5**: https://getbootstrap.com/docs/5.3/

## 💡 Example Prompts

Try these prompts in the UI:

- "Summarize this document in 5 bullet points"
- "Create a professional executive summary"
- "Extract all key dates and events"
- "Rewrite this content for a teenager"
- "Generate discussion points from this article"
- "Create an FAQ based on this document"

## 📧 Support

If you encounter issues:
1. Check the console for error messages
2. Review README.md for detailed docs
3. Check Gemini API status: https://status.cloud.google.com/

---

Happy document generating! 🎉
