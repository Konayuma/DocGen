from typing import Optional
from openai import OpenAI
from docgen.config import config
from docgen.services.pdf_generator import PDFGenerator


class OpenRouterClient:
    """Client for interacting with OpenRouter API."""
    
    def __init__(self):
        """Initialize OpenRouter client with API key."""
        if not config.OPENROUTER_API_KEY:
            raise ValueError("OpenRouter API key not configured")
        self.client = OpenAI(
            api_key=config.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )
        # Keep base URL handy for direct model list fetch
        self._base_url = "https://openrouter.ai/api/v1"
    
    def generate_content(
        self,
        prompt: str,
        extracted_text: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> dict:
        """
        Generate content using OpenRouter API.
        
        Args:
            prompt: User's instruction/prompt
            extracted_text: Text extracted from uploaded document
            model: Model name (default: from config)
            temperature: Creativity level (0-2)
            max_tokens: Maximum tokens in response
        
        Returns:
            dict with keys: text, tokens_input, tokens_output, model_used, finish_reason
        """
        model_name = model or config.OPENROUTER_MODEL
        
        # Build messages
        if extracted_text and extracted_text.strip():
            user_content = f"""SOURCE MATERIAL:
{extracted_text}

---

USER INSTRUCTION:
{prompt}

Generate the document content now:"""
        else:
            user_content = f"""USER INSTRUCTION:
{prompt}

Generate the document content now:"""
        
        messages = [
            {
                "role": "system",
                "content": "You are a professional document writer. Create well-structured, polished content with proper hierarchy and flow.\n\nFORMATTING REQUIREMENTS (IMPORTANT - NO MARKDOWN SYNTAX):\n- Do NOT use markdown syntax (no #, ##, ###, **, __, *, _, `).\n- Use THREE levels of headings as PLAIN TEXT:\n  * MAJOR SECTION HEADINGS IN ALL CAPS for main topics\n  * Section Heading: Use colon at end for subsections\n  * 1. Numbered Item for sub-subsections\n- Write coherent paragraphs between sections\n- Bullet/list items use format: - Item (dash space)\n- Create tables using PLAIN TEXT pipe format: | Column 1 | Column 2 | Column 3 |\n- Each table row on new line with | separators\n- Avoid AI preambles like \"Here is...\", \"Based on...\", \"In this document...\", etc.\n- Write naturally and professionally, plain text only"
            },
            {
                "role": "user",
                "content": user_content
            }
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            text_content = response.choices[0].message.content or ""
            
            if not text_content:
                raise ValueError("Empty response from OpenRouter. Try a different prompt.")
            
            # Clean up AI footprint and markdown artifacts
            text_content = PDFGenerator.clean_ai_output(text_content)
            
            result = {
                "text": text_content,
                "tokens_input": response.usage.prompt_tokens if response.usage else 0,
                "tokens_output": response.usage.completion_tokens if response.usage else 0,
                "model_used": model_name,
                "finish_reason": response.choices[0].finish_reason or "unknown",
            }
            
            return result
        except Exception as e:
            raise ValueError(f"OpenRouter API error: {str(e)}")
    
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
            # Rate limit: wait 1 second between requests
            time.sleep(1)
            
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
            "model_used": model or config.OPENROUTER_MODEL,
            "chunks_generated": len(all_text),
        }
    
    def estimate_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Estimate token count for given text.
        
        Args:
            text: Text to estimate
            model: Model name (unused, for interface compatibility)
        
        Returns:
            Estimated token count
        """
        # Rough estimate: ~4 characters per token for English text
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

    def list_models(self) -> list:
        """
        List available models for this OpenRouter key.
        Returns list of dicts: { id, name }
        """
        import requests

        url = f"{self._base_url}/models"
        headers = {"Authorization": f"Bearer {config.OPENROUTER_API_KEY}"}

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            models = []
            # OpenRouter models endpoint may return an array under 'data' or 'models'
            items = data.get('data') or data.get('models') or data
            for m in items:
                mid = m.get('id') or m.get('model_id') or m.get('name')
                name = m.get('name') or m.get('id') or mid
                if mid:
                    models.append({"id": mid, "name": name})
            return models
        except Exception as e:
            # Best effort: return empty list on failure
            print(f"[WARN] Could not fetch OpenRouter models: {e}")
            return []
