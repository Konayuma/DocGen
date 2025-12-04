from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
import os
from pathlib import Path
from datetime import datetime

from docgen.config import config
from docgen.routers import document
from docgen.utils import cleanup_old_files

# Initialize FastAPI app
app = FastAPI(
    title="DocGen",
    description="AI-powered document generator using Gemini API",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup Jinja2 templates
template_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=template_dir)

# Mount static files BEFORE including routes
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
(static_dir / "css").mkdir(exist_ok=True)  # Ensure css subdirectory exists
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routes AFTER static mount
app.include_router(document.router)


@app.on_event("startup")
async def startup_event():
    """Cleanup old temp files on startup."""
    cleanup_old_files(config.TEMP_DIR, config.UPLOAD_RETENTION_SECONDS)
    
    # Validate API key by attempting to access Gemini
    try:
        import google.generativeai as genai
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel(config.GEMINI_MODEL)
        # Quick test call to verify API key works
        response = model.count_tokens("test")
        print(f"✓ Gemini API key validated successfully")
    except Exception as e:
        print(f"⚠ WARNING: Gemini API key validation failed: {str(e)}")
        print(f"⚠ Please verify your API key in the .env file")
        print(f"⚠ Get a key from: https://aistudio.google.com/apikey")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve main upload page."""
    return templates.TemplateResponse("index.html", {"request": request, "debug": config.DEBUG})


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
    }


@app.get("/api/info")
async def api_info():
    """Get API information."""
    return {
        "name": "DocGen",
        "version": "1.0.0",
        "description": "AI-powered document generator",
        "models_available": [config.GEMINI_MODEL],
        "max_file_size_mb": config.MAX_FILE_SIZE_MB,
        "supported_formats": list(config.ALLOWED_EXTENSIONS),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=config.DEBUG)
