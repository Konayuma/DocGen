from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.responses import FileResponse, JSONResponse
import uuid
import os
from datetime import datetime
from typing import Dict, Any

from docgen.config import config
from docgen.services.extraction import TextExtractor
from docgen.services.gemini_client import GeminiClient
from docgen.services.openai_client import OpenAIClient
from docgen.services.openrouter_client import OpenRouterClient
from docgen.services.pdf_generator import PDFGenerator
from docgen.models.schemas import (
    UploadResponse,
    GenerateResponse,
    JobStatusResponse,
    ErrorResponse,
    GenerateRequest,
    FileUploadResponse,
)
from docgen.utils import is_allowed_extension, format_file_size

# In-memory storage (for MVP; use database in production)
UPLOADS: Dict[str, Dict[str, Any]] = {}
JOBS: Dict[str, Dict[str, Any]] = {}
GENERATED_PDFS: Dict[str, Dict[str, Any]] = {}

router = APIRouter()


@router.get("/providers")
async def get_available_providers():
    """Get available AI providers and their models."""
    providers = {}
    
    if config.has_gemini:
        providers["gemini"] = {
            "name": "Google Gemini",
            "models": [
                {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash"},
                {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro"},
                {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash"},
            ],
            "default": config.GEMINI_MODEL,
        }
    
    if config.has_openai:
        providers["openai"] = {
            "name": "OpenAI",
            "models": [
                {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
                {"id": "gpt-4o", "name": "GPT-4o"},
                {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"},
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
            ],
            "default": config.OPENAI_MODEL,
        }
    
    if config.has_openrouter:
        # Start with a default static set
        static_models = [
            {"id": "amazon/nova-2-lite-v1:free", "name": "Amazon Nova 2 Lite v1 (free)"},
            {"id": "tngtech/deepseek-r1t-chimera:free", "name": "DeepSeek R1T Chimera (free)"},
            {"id": "openai/gpt-oss-20b:free", "name": "GPT-OSS 20B (free)"},
            {"id": "qwen/qwen3-coder:free", "name": "Qwen3 Coder (free)"},
            {"id": "nvidia/nemotron-nano-9b-v2:free", "name": "NemoTron Nano 9B v2 (free)"},
            {"id": "meituan/longcat-flash-chat:free", "name": "LongCat Flash Chat (free)"},
        ]

        # Try to fetch the available models for the user's OpenRouter API key
        try:
            openrouter_client = OpenRouterClient()
            available_models = openrouter_client.list_models() or []
        except Exception as e:
            # If we fail to fetch remote models, log and fall back to static_models
            print(f"[WARN] Could not fetch OpenRouter models dynamically: {e}")
            available_models = []

        # Build a merged model list: dynamic models first, then static ones (avoiding duplicates)
        merged = []
        seen_ids = set()
        for m in (available_models or []):
            if m.get('id') and m['id'] not in seen_ids:
                merged.append({"id": m['id'], "name": m.get('name', m['id'])})
                seen_ids.add(m['id'])
        for m in static_models:
            if m['id'] not in seen_ids:
                merged.append(m)
                seen_ids.add(m['id'])

        providers["openrouter"] = {
            "name": "OpenRouter",
            "models": merged,
            "default": config.OPENROUTER_MODEL,
        }
    
    return {"providers": providers}


@router.post("/upload", response_model=UploadResponse)
async def upload_files(files: list[UploadFile] = File(...), upload_id: str = Form(None)):
    """
    Upload and extract text from one or more documents.
    
    Supported formats: PDF, DOCX, TXT, PNG, JPG, JPEG, BMP, TIFF
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # If files are appended to an existing upload, reuse the upload_id
    if upload_id and upload_id in UPLOADS:
        existing = UPLOADS[upload_id]
        uploaded_files = existing.get('files', [])
        total_chars = existing.get('total_chars', 0)
    else:
        upload_id = str(uuid.uuid4())
        uploaded_files = []
        total_chars = 0
    
    try:
        for file in files:
            # Validate file extension
            if not is_allowed_extension(file.filename):
                raise HTTPException(
                    status_code=400,
                    detail=f"File '{file.filename}' has unsupported extension",
                )
            
            # Read file content
            content = await file.read()
            
            # Validate file size
            if len(content) > config.MAX_FILE_SIZE_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail=f"File '{file.filename}' exceeds max size ({format_file_size(config.MAX_FILE_SIZE_BYTES)})",
                )
            
            # Save temp file for extraction
            temp_dir = config.TEMP_DIR
            os.makedirs(temp_dir, exist_ok=True)
            temp_filepath = os.path.join(temp_dir, f"{upload_id}_{file.filename}")
            
            with open(temp_filepath, "wb") as f:
                f.write(content)
            
            # Extract text
            try:
                extracted_text, metadata = TextExtractor.extract(temp_filepath)
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            
            # Store file info
            file_info = {
                "filename": file.filename,
                "temp_path": temp_filepath,
                "extracted_text": extracted_text,
                "size_bytes": len(content),
                "char_count": len(extracted_text),
                "page_count": metadata.get("pages", 1),
                "extraction_method": metadata.get("extraction_method", "unknown"),
            }
            
            uploaded_files.append(file_info)
            total_chars += len(extracted_text)
        
        # Combine all extracted text (append if existing)
        combined_text = "\n\n".join([f["extracted_text"] for f in uploaded_files])
        
        # Store in memory
        UPLOADS[upload_id] = {
            "files": uploaded_files,
            "combined_text": combined_text,
            "total_chars": total_chars,
            "timestamp": datetime.now(),
        }
        
        # Prepare response
        response_files = [
            FileUploadResponse(
                filename=f["filename"],
                size_bytes=f["size_bytes"],
                extraction_method=f["extraction_method"],
                char_count=f["char_count"],
                page_count=f["page_count"],
            )
            for f in uploaded_files
        ]
        
        return UploadResponse(
            upload_id=upload_id,
            files=response_files,
            total_chars=total_chars,
            timestamp=datetime.now(),
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/generate", response_model=GenerateResponse)
async def generate_document(request: GenerateRequest, background_tasks: BackgroundTasks):
    """
    Generate a document using AI with optional extracted text and user prompt.
    
    If upload_id is not provided, generates from prompt only.
    
    Returns job_id for polling status.
    """
    # Validate upload exists (if provided)
    if request.upload_id and request.upload_id not in UPLOADS:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    # Create job
    job_id = str(uuid.uuid4())
    
    JOBS[job_id] = {
        "upload_id": request.upload_id or None,
        "status": "processing",
        "progress": 0,
        "error": None,
        "result": None,
        "timestamp": datetime.now(),
    }
    
    # Schedule generation as background task
    background_tasks.add_task(
        _generate_task,
        job_id=job_id,
        upload_id=request.upload_id,
        prompt=request.prompt,
        title=request.title or "Generated Document",
        provider=request.provider or "gemini",
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        length=request.length or 1,
    )
    
    return GenerateResponse(
        job_id=job_id,
        upload_id=request.upload_id,
        status="processing",
        timestamp=datetime.now(),
    )


async def _generate_task(
    job_id: str,
    upload_id: str,
    prompt: str,
    title: str = "Generated Document",
    provider: str = "gemini",
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    length: int = 1,
):
    """Background task for document generation."""
    try:
        JOBS[job_id]["progress"] = 10
        
        # Get extracted text (if upload provided)
        if upload_id and upload_id in UPLOADS:
            upload_data = UPLOADS[upload_id]
            extracted_text = upload_data["combined_text"]
            source_files = upload_data.get("files", [])
        else:
            # No upload - generate from prompt only
            extracted_text = ""
            source_files = []
        
        JOBS[job_id]["progress"] = 20
        
        # Select the appropriate client based on provider
        if provider == "openai":
            if not config.has_openai:
                raise ValueError("OpenAI API key not configured")
            client = OpenAIClient()
        elif provider == "openrouter":
            if not config.has_openrouter:
                raise ValueError("OpenRouter API key not configured")
            client = OpenRouterClient()
        else:
            if not config.has_gemini:
                raise ValueError("Gemini API key not configured")
            client = GeminiClient()
        
        # Use long generation if length > 1
        if length > 1:
            result = client.generate_long_content(
                prompt=prompt,
                extracted_text=extracted_text,
                target_length=length,
                model=model,
                temperature=temperature,
            )
            # Update progress gradually during chunked generation
            progress_per_chunk = 50 // length
            JOBS[job_id]["progress"] = 20 + (progress_per_chunk * result.get("chunks_generated", 1))
        else:
            result = client.generate_content(
                prompt=prompt,
                extracted_text=extracted_text,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        
        JOBS[job_id]["progress"] = 70
        
        # Use the user-provided title
        document_title = title or "Generated Document"
        
        JOBS[job_id]["progress"] = 75
        
        # Generate PDF
        metadata = {
            "title": document_title,
            "extraction_info": {
                "filename": ", ".join([f["filename"] for f in source_files]) if source_files else "Generated from prompt",
                "extraction_method": source_files[0].get("extraction_method", "unknown") if source_files else "prompt-only",
            },
            "tokens_used": {
                "input": result["tokens_input"],
                "output": result["tokens_output"],
            },
            "model": result["model_used"],
        }
        
        pdf_bytes = PDFGenerator.generate_pdf(
            content=result["text"],
            title=document_title,
            metadata=metadata,
        )
        
        JOBS[job_id]["progress"] = 90
        
        # Store PDF
        pdf_dir = os.path.join(config.TEMP_DIR, "generated")
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_filepath = os.path.join(pdf_dir, f"{job_id}.pdf")
        
        PDFGenerator.save_pdf(pdf_bytes, pdf_filepath)
        
        # Update job
        JOBS[job_id].update({
            "status": "completed",
            "progress": 100,
            "result": {
                "pdf_filepath": pdf_filepath,
                "generated_text": result["text"],
                "tokens_input": result["tokens_input"],
                "tokens_output": result["tokens_output"],
            },
            "completion_time": datetime.now(),
        })
        
        # Store PDF info for download
        GENERATED_PDFS[job_id] = {
            "filepath": pdf_filepath,
            "filename": f"generated_{job_id[:8]}.pdf",
        }
    
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Job {job_id} failed: {error_msg}")  # Debug logging
        JOBS[job_id].update({
            "status": "failed",
            "error": error_msg,
            "completion_time": datetime.now(),
        })


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get status of a generation job."""
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = JOBS[job_id]
    print(f"[STATUS] Job {job_id}: status={job['status']}, progress={job['progress']}, error={job.get('error')}")  # Debug
    
    return JobStatusResponse(
        job_id=job_id,
        upload_id=job["upload_id"],
        status=job["status"],
        progress=job["progress"],
        error=job["error"],
        completion_time=job.get("completion_time"),
    )


@router.get("/download/{job_id}")
async def download_pdf(job_id: str):
    """Download generated PDF."""
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = JOBS[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed (status: {job['status']})",
        )
    
    if job_id not in GENERATED_PDFS:
        raise HTTPException(status_code=410, detail="PDF file not found or expired")
    
    pdf_info = GENERATED_PDFS[job_id]
    filepath = pdf_info["filepath"]
    filename = pdf_info["filename"]
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=410, detail="PDF file not found")
    
    return FileResponse(
        filepath,
        media_type="application/pdf",
        filename=filename,
    )
