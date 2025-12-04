from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


class FileUploadResponse(BaseModel):
    """Response model for file upload."""
    filename: str
    size_bytes: int
    extraction_method: str
    char_count: int
    page_count: int


class UploadResponse(BaseModel):
    """Response model for upload endpoint."""
    upload_id: str
    files: List[FileUploadResponse]
    total_chars: int
    timestamp: datetime


class GenerateRequest(BaseModel):
    """Request model for content generation."""
    upload_id: Optional[str] = None
    prompt: str = Field(..., min_length=1, max_length=2000)
    title: Optional[str] = Field("Generated Document", max_length=200, description="Document title")
    provider: Optional[Literal["gemini", "openai", "openrouter"]] = Field("gemini", description="AI provider to use")
    model: Optional[str] = None
    temperature: Optional[float] = Field(0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(2048, ge=100, le=4096)
    length: Optional[int] = Field(1, ge=1, le=5, description="Number of generation chunks (1-5, each ~2000 tokens)")


class GenerateResponse(BaseModel):
    """Response model for generation start."""
    job_id: str
    upload_id: Optional[str] = None
    status: str = "processing"
    timestamp: datetime


class JobStatusResponse(BaseModel):
    """Response model for job status."""
    job_id: str
    upload_id: Optional[str] = None
    status: str  # processing, completed, failed
    progress: int = 0  # 0-100
    error: Optional[str] = None
    completion_time: Optional[datetime] = None


class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime
