from typing import Optional
import google.generativeai as genai
from docgen.config import config
from docgen.services.pdf_generator import PDFGenerator


class GeminiClient:
    """Client for interacting with Google Gemini API."""
    
    def __init__(self):
        """Initialize Gemini client with API key."""
        genai.configure(api_key=config.GEMINI_API_KEY)
    
    def generate_content(
        self,
        prompt: str,
        extracted_text: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> dict:
        """
        Generate content using Gemini API.
        
        Args:
            prompt: User's instruction/prompt
            extracted_text: Text extracted from uploaded document
            model: Model name (default: from config)
            temperature: Creativity level (0-2)
            max_tokens: Maximum tokens in response
        
        Returns:
            dict with keys: text, tokens_input, tokens_output, model_used, finish_reason
        """
        model_name = model or config.GEMINI_MODEL
        
        # Combine prompt with extracted text
        if extracted_text and extracted_text.strip():
            full_prompt = f"""You are a professional document writer. Create well-structured, polished content with proper hierarchy and flow.

FORMATTING REQUIREMENTS (IMPORTANT - NO MARKDOWN SYNTAX):
- Do NOT use markdown syntax (no #, ##, ###, **, __, *, _, `).
- Use THREE levels of headings as PLAIN TEXT:
  * MAJOR SECTION HEADINGS IN ALL CAPS for main topics
  * Section Heading: Use colon at end for subsections  
  * 1. Numbered Item for sub-subsections
- Write coherent paragraphs between sections
- Bullet/list items use format: - Item (dash space)
- Create tables using PLAIN TEXT pipe format: | Column 1 | Column 2 | Column 3 |
- Each table row on new line with | separators
- Avoid AI preambles like "Here is...", "Based on...", "In this document...", etc.
- Write naturally and professionally, plain text only

SOURCE MATERIAL:
{extracted_text}

---

USER INSTRUCTION:
{prompt}

Generate the document content now:"""
        else:
            full_prompt = f"""You are a professional document writer. Create well-structured, polished content with proper hierarchy and flow.

FORMATTING REQUIREMENTS (IMPORTANT - NO MARKDOWN SYNTAX):
- Do NOT use markdown syntax (no #, ##, ###, **, __, *, _, `).
- Use THREE levels of headings as PLAIN TEXT:
  * MAJOR SECTION HEADINGS IN ALL CAPS for main topics
  * Section Heading: Use colon at end for subsections
  * 1. Numbered Item for sub-subsections
- Write coherent paragraphs between sections
- Bullet/list items use format: - Item (dash space)
- Create tables using PLAIN TEXT pipe format: | Column 1 | Column 2 | Column 3 |
- Each table row on new line with | separators
- Avoid AI preambles like "Here is...", "Based on...", "In this document...", etc.
- Write naturally and professionally, plain text only

USER INSTRUCTION:
{prompt}

Generate the document content now:"""
        
        try:
            response = genai.GenerativeModel(model_name).generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
            
            # Extract metadata
            text_content = ""
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'text'):
                            text_content += part.text
            
            if not text_content:
                # Response was blocked or empty
                finish_reason = response.candidates[0].finish_reason.name if response.candidates else "UNKNOWN"
                raise ValueError(f"Empty response from Gemini (finish_reason: {finish_reason}). The request may have been blocked by safety filters. Try a different prompt.")
            
            # Clean up AI footprint and markdown artifacts
            text_content = PDFGenerator.clean_ai_output(text_content)
            
            result = {
                "text": text_content,
                "tokens_input": response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                "tokens_output": response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
                "model_used": model_name,
                "finish_reason": response.candidates[0].finish_reason.name if response.candidates else "UNKNOWN",
            }
            
            return result
        except Exception as e:
            raise ValueError(f"Gemini API error: {str(e)}")
    
    def generate_long_content(
        self,
        prompt: str,
        extracted_text: str,
        target_length: int = 3,
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> dict:
        """
        Generate longer content by making multiple calls with continuation prompts.
        
        Args:
            prompt: User's instruction/prompt
            extracted_text: Text extracted from uploaded document
            target_length: Number of continuation chunks (1-5, each ~2000 tokens)
            model: Model name (default: from config)
            temperature: Creativity level (0-2)
        
        Returns:
            dict with keys: text, tokens_input, tokens_output, model_used, chunks_generated
        """
        import time
        
        # Limit chunks to avoid excessive API calls
        target_length = max(1, min(target_length, 5))
        
        all_text = []
        total_input_tokens = 0
        total_output_tokens = 0
        
        # First generation with original prompt
        result = self.generate_content(
            prompt=prompt,
            extracted_text=extracted_text,
            model=model,
            temperature=temperature,
            max_tokens=2048,
        )
        
        all_text.append(result["text"])
        total_input_tokens += result["tokens_input"]
        total_output_tokens += result["tokens_output"]
        
        # Generate continuations if requested
        for i in range(1, target_length):
            # Rate limit: wait 2 seconds between requests (Gemini free tier: ~15 RPM)
            time.sleep(2)
            
            continuation_prompt = f"""Continue and expand on the previous response. Provide additional details, examples, or related information that completes the document comprehensively.

Previous content:
{all_text[-1][-500:]}

Continue with more content:"""
            
            try:
                result = self.generate_content(
                    prompt=continuation_prompt,
                    extracted_text="",  # Don't repeat source on continuation
                    model=model,
                    temperature=temperature,
                    max_tokens=2048,
                )
                
                all_text.append(result["text"])
                total_input_tokens += result["tokens_input"]
                total_output_tokens += result["tokens_output"]
            except Exception as e:
                # If continuation fails, just return what we have
                print(f"[WARN] Continuation {i+1} failed: {e}")
                break
        
        return {
            "text": "\n\n".join(all_text),
            "tokens_input": total_input_tokens,
            "tokens_output": total_output_tokens,
            "model_used": model or config.GEMINI_MODEL,
            "chunks_generated": len(all_text),
        }
    
    def estimate_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Estimate token count for given text.
        
        Args:
            text: Text to estimate
            model: Model name (default: from config)
        
        Returns:
            Estimated token count
        """
        model_name = model or config.GEMINI_MODEL
        
        try:
            response = genai.GenerativeModel(model_name).count_tokens(text)
            return response.total_tokens
        except Exception as e:
            # Fallback: rough estimate
            return len(text) // 4
    
    def generate_title(self, content: str, model: Optional[str] = None) -> str:
        """
        Generate a concise, relevant title from content.
        
        Args:
            content: The document content to generate a title for
            model: Model name (default: from config)
        
        Returns:
            Generated title string (max 60 characters)
        """
        title_prompt = f"""Generate a concise, professional title (max 6 words) for this document content. 
Return ONLY the title, nothing else. No quotes, no explanations.

Content preview:
{content[:500]}

Title:"""
        
        try:
            result = self.generate_content(
                prompt=title_prompt,
                extracted_text="",
                model=model,
                temperature=0.3,  # Lower for consistency
                max_tokens=20,
            )
            title = result["text"].strip().strip('"').strip("'")
            if len(title) > 60:
                title = title[:57] + "..."
            return title if title else "Document"
        except Exception as e:
            print(f"[WARN] Title generation failed: {e}")
            return "Document"
