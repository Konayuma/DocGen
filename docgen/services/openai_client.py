from typing import Optional
from openai import OpenAI
from docgen.config import config
from docgen.services.pdf_generator import PDFGenerator


class OpenAIClient:
    """Client for interacting with OpenAI API (via OpenAI Python SDK)."""

    def __init__(self):
        if not config.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not configured")
        # Initialize OpenAI SDK client
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)

    def generate_content(
        self,
        prompt: str,
        extracted_text: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> dict:
        model_name = model or config.OPENAI_MODEL

        if extracted_text and extracted_text.strip():
            user_content = f"SOURCE MATERIAL:\n{extracted_text}\n\n---\n\nUSER INSTRUCTION:\n{prompt}\n\nGenerate the document content now:"
        else:
            user_content = f"USER INSTRUCTION:\n{prompt}\n\nGenerate the document content now:"
        
        messages = [
            {"role": "system", "content": "You are a professional document writer. Create well-structured, polished content with proper hierarchy and flow.\n\nFORMATTING REQUIREMENTS (IMPORTANT - NO MARKDOWN SYNTAX):\n- Do NOT use markdown syntax (no #, ##, ###, **, __, *, _, `).\n- Use THREE levels of headings as PLAIN TEXT:\n  * MAJOR SECTION HEADINGS IN ALL CAPS for main topics\n  * Section Heading: Use colon at end for subsections\n  * 1. Numbered Item for sub-subsections\n- Write coherent paragraphs between sections\n- Bullet/list items use format: - Item (dash space)\n- Create tables using PLAIN TEXT pipe format: | Column 1 | Column 2 | Column 3 |\n- Each table row on new line with | separators\n- Avoid AI preambles like \"Here is...\", \"Based on...\", \"In this document...\", etc.\n- Write naturally and professionally, plain text only"},
            {"role": "user", "content": user_content},
        ]

        try:
            # Using OpenAI SDK's chat 'completions' endpoint via client
            response = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            text_content = response.choices[0].message.content or ""
            if not text_content:
                raise ValueError("Empty response from OpenAI API")

            text_content = PDFGenerator.clean_ai_output(text_content)

            usage = getattr(response, 'usage', None) or {}
            result = {
                "text": text_content,
                "tokens_input": usage.get('prompt_tokens', 0),
                "tokens_output": usage.get('completion_tokens', 0),
                "model_used": model_name,
                "finish_reason": response.choices[0].finish_reason or 'unknown',
            }

            return result
        except Exception as e:
            raise ValueError(f"OpenAI API error: {str(e)}")

    def generate_long_content(self, prompt: str, extracted_text: str, target_length: int = 3, model: Optional[str] = None, temperature: float = 0.7) -> dict:
        import time
        target_length = max(1, min(target_length, 5))
        all_text, total_input_tokens, total_output_tokens = [], 0, 0

        result = self.generate_content(prompt, extracted_text, model=model, temperature=temperature, max_tokens=2048)
        all_text.append(result['text'])
        total_input_tokens += result['tokens_input']
        total_output_tokens += result['tokens_output']

        for i in range(1, target_length):
            time.sleep(1)
            continuation_prompt = f"Continue and expand on the previous response. Additional details and examples are helpful.\n\nPrevious content:\n{all_text[-1][-500:]}\n\nContinue with more content:"
            try:
                res = self.generate_content(continuation_prompt, '', model=model, temperature=temperature, max_tokens=2048)
                all_text.append(res['text'])
                total_input_tokens += res['tokens_input']
                total_output_tokens += res['tokens_output']
            except Exception as e:
                break

        return {
            'text': '\n\n'.join(all_text),
            'tokens_input': total_input_tokens,
            'tokens_output': total_output_tokens,
            'model_used': model or config.OPENAI_MODEL,
            'chunks_generated': len(all_text),
        }

    def estimate_tokens(self, text: str, model: Optional[str] = None) -> int:
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
