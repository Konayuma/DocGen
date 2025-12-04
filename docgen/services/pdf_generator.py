import os
import html
from io import BytesIO
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
    Image as RLImage,
)
from reportlab.lib import colors
from datetime import datetime


class PDFGenerator:
    """Service for generating PDF documents with ReportLab."""
    
    # Define styles
    STYLES = getSampleStyleSheet()
    
    # Add custom styles
    TITLE_STYLE = ParagraphStyle(
        "CustomTitle",
        parent=STYLES["Heading1"],
        fontSize=24,
        textColor=HexColor("#1f3a70"),
        spaceAfter=20,
        alignment=1,  # Center
    )
    
    HEADING_STYLE = ParagraphStyle(
        "CustomHeading",
        parent=STYLES["Heading2"],
        fontSize=14,
        textColor=HexColor("#2c5aa0"),
        spaceAfter=12,
        spaceBefore=12,
    )
    
    BODY_STYLE = ParagraphStyle(
        "CustomBody",
        parent=STYLES["BodyText"],
        fontSize=11,
        alignment=4,  # Justify
        spaceAfter=12,
        leading=16,
    )
    
    SUBHEADING_STYLE = ParagraphStyle(
        "CustomSubheading",
        parent=STYLES["Heading3"],
        fontSize=12,
        textColor=HexColor("#4a5568"),
        spaceAfter=8,
        spaceBefore=10,
        bold=True,
    )
    
    SUBHEADING2_STYLE = ParagraphStyle(
        "CustomSubheading2",
        parent=STYLES["Heading3"],
        fontSize=11,
        textColor=HexColor("#5a6b7a"),
        spaceAfter=6,
        spaceBefore=8,
        bold=True,
    )
    
    QUOTE_STYLE = ParagraphStyle(
        "CustomQuote",
        parent=STYLES["BodyText"],
        fontSize=10,
        leftIndent=30,
        rightIndent=30,
        textColor=HexColor("#4a5568"),
        spaceAfter=12,
        fontName="Helvetica-Oblique",
    )
    
    @staticmethod
    def clean_ai_output(text: str) -> str:
        """Remove markdown syntax and AI footprint from generated content."""
        import re
        
        # Remove common AI preambles
        ai_phrases = [
            r"^(Okay|Sure|Of course|Certainly|Here('s| is| are)|I('ll| will| can| have)|Let me)[^.]*[.:!]\s*",
            r"^Based on (the|your)[^.]*[.:!]\s*",
            r"^This (document|report|summary)[^.]*[.:!]\s*",
            r"---+\s*",
            r"\*\*\*+\s*",
        ]
        
        for pattern in ai_phrases:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)
        
        # IMPORTANT: Convert markdown headers to our format BEFORE removing the # symbols
        # ### or ##: Section Heading -> Section Heading: (for section headings)
        text = re.sub(r"^###\s+([^\n]+?):\s*$", r"\1:", text, flags=re.MULTILINE)
        # ### Heading -> HEADING (for major headings if all caps words)
        text = re.sub(r"^###\s+([A-Z\s&]+?)(:?)?\s*$", lambda m: m.group(1).upper() + (":" if m.group(2) else ""), text, flags=re.MULTILINE)
        # ## Section: -> Section:
        text = re.sub(r"^##\s+([^\n]+?)(:?)?\s*$", lambda m: m.group(1) + (":" if m.group(2) else ":"), text, flags=re.MULTILINE)
        # # Heading -> HEADING (major section)
        text = re.sub(r"^#\s+([^\n:]+?)\s*$", lambda m: m.group(1).upper(), text, flags=re.MULTILINE)
        
        # Now remove any remaining markdown headers
        text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
        
        # Remove bold markdown (**text** or __text__ -> text)
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"__([^_]+)__", r"\1", text)
        
        # Remove italic markdown (*text* or _text_ -> text) - be careful not to affect lists
        text = re.sub(r"(?<!\*)\*(?!\*)([^*]+)(?<!\*)\*(?!\*)", r"\1", text)
        text = re.sub(r"(?<!_)_(?!_)([^_]+)(?<!_)_(?!_)", r"\1", text)
        
        # Remove inline code (`code` -> code)
        text = re.sub(r"`([^`]+)`", r"\1", text)
        
        # Remove code blocks
        text = re.sub(r"```[\s\S]*?```", "", text)
        
        # Remove links [text](url) -> text
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        
        # Clean up excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        
        return text.strip()
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """Sanitize text for Paragraph (escape special chars)."""
        return html.escape(text, quote=True)
    
    @staticmethod
    def generate_pdf(
        content: str,
        title: str = "Generated Document",
        author: str = "DocGen",
        subject: str = "AI-Generated Document",
        metadata: dict = None,
    ) -> bytes:
        """
        Generate PDF from content text.
        
        Args:
            content: Main body text to include in PDF
            title: Document title
            author: Document author
            subject: Document subject
            metadata: Optional dict with extraction_info, tokens_used, etc.
        
        Returns:
            PDF as bytes
        """
        # Create PDF in memory
        pdf_buffer = BytesIO()
        
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=1 * inch,
            bottomMargin=0.75 * inch,
            title=title,
            author=author,
            subject=subject,
        )
        
        # Build story (document elements)
        story = []
        
        # Add title
        sanitized_title = PDFGenerator.sanitize_text(title)
        story.append(Paragraph(sanitized_title, PDFGenerator.TITLE_STYLE))
        story.append(Spacer(1, 0.4 * inch))
        
        # Add main content with intelligent formatting (no metadata header - cleaner look)
        story.extend(PDFGenerator._format_content(content))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
    
    @staticmethod
    def _format_content(content: str) -> list:
        """Format content with smart detection of headings, lists, tables, and paragraphs."""
        import re
        
        # Clean AI footprint and markdown first
        content = PDFGenerator.clean_ai_output(content)
        
        story = []
        lines = content.split("\n")
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
            
            # Detect table data (pipe-separated or pipe-bordered lines)
            if "|" in line and len(line) > 5:
                # Collect table rows
                table_rows = []
                while i < len(lines):
                    curr_line = lines[i].strip()
                    
                    # Skip separator lines (e.g., |---|---|---|)
                    if curr_line and "|" in curr_line and re.match(r"^\|[\s\-|]+\|$", curr_line):
                        i += 1
                        continue
                    
                    # Collect actual table rows
                    if curr_line and "|" in curr_line and curr_line.count("|") >= 2:
                        # Parse pipe-separated values
                        cells = [cell.strip() for cell in curr_line.split("|")]
                        cells = [c for c in cells if c]  # Remove empty cells from edges
                        if cells and len(cells) >= 2:  # Must have at least 2 columns
                            table_rows.append(cells)
                        i += 1
                    elif not curr_line:
                        i += 1
                        break
                    else:
                        break
                
                # Create and style table
                if table_rows and len(table_rows) >= 2:  # Need at least header + 1 row
                    story.append(Spacer(1, 0.15 * inch))
                    
                    # Wrap cell content in Paragraphs for proper text wrapping
                    # This prevents truncation and allows dynamic cell expansion
                    wrapped_rows = []
                    
                    # Header row styling
                    header_style = ParagraphStyle(
                        'TableHeader',
                        parent=PDFGenerator.STYLES['Normal'],
                        fontSize=10,
                        textColor=colors.whitesmoke,
                        alignment=0,  # Left align
                        spaceAfter=0,
                        spaceBefore=0,
                        leading=12,
                    )
                    
                    # Body cell styling
                    cell_style = ParagraphStyle(
                        'TableCell',
                        parent=PDFGenerator.STYLES['Normal'],
                        fontSize=9,
                        alignment=0,  # Left align
                        spaceAfter=0,
                        spaceBefore=0,
                        leading=11,
                    )
                    
                    for row_idx, row in enumerate(table_rows):
                        wrapped_row = []
                        for cell_text in row:
                            if row_idx == 0:
                                # Header cell
                                para = Paragraph(PDFGenerator.sanitize_text(cell_text), header_style)
                            else:
                                # Body cell
                                para = Paragraph(PDFGenerator.sanitize_text(cell_text), cell_style)
                            wrapped_row.append(para)
                        wrapped_rows.append(wrapped_row)
                    
                    # Set column widths - use reasonable defaults that fit page width
                    # Letter page is 8.5", minus 1.5" margins = 7" available
                    num_cols = len(table_rows[0])
                    # Distribute columns evenly, with minimum width to prevent squashing
                    col_width = (7.0 * inch) / num_cols
                    col_widths = [col_width] * num_cols
                    
                    table = Table(wrapped_rows, colWidths=col_widths)
                    
                    # Style table with professional appearance
                    table.setStyle(TableStyle([
                        # Header row styling
                        ('BACKGROUND', (0, 0), (-1, 0), HexColor("#2c5aa0")),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('TOPPADDING', (0, 0), (-1, 0), 10),
                        ('LEFTPADDING', (0, 0), (-1, 0), 8),
                        ('RIGHTPADDING', (0, 0), (-1, 0), 8),
                        
                        # Body row styling
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor("#f8fafc")]),
                        ('TOPPADDING', (0, 1), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                        ('LEFTPADDING', (0, 1), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 1), (-1, -1), 8),
                        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
                        
                        # Grid lines
                        ('GRID', (0, 0), (-1, -1), 1, HexColor("#d0d0d0")),
                        ('LINEABOVE', (0, 0), (-1, 0), 2, HexColor("#2c5aa0")),
                        ('LINEBELOW', (0, -1), (-1, -1), 2, HexColor("#2c5aa0")),
                    ]))
                    
                    story.append(table)
                    story.append(Spacer(1, 0.15 * inch))
                continue
            
            # Detection logic (order matters - check specific patterns first):
            
            # 1. Major headings: ALL CAPS, short, no period, substantial length
            is_major_heading = (line.isupper() and 
                               len(line) < 80 and 
                               len(line) > 5 and
                               not line.endswith(".") and 
                               not line.endswith(":") and
                               not line.startswith(("- ", "• ", "* ", "1.", "2.", "3.")) and
                               line.count(" ") >= 1)  # At least 2 words
            
            # 2. Section headings: ends with colon (e.g., "Introduction to Database Normalization:")
            is_section_heading = (line.endswith(":") and 
                                 len(line) < 100 and 
                                 not line.startswith(("- ", "• ", "* ")) and
                                 not line.isupper() and
                                 len(line) > 3)  # Meaningful length
            
            # 3. Subsection headings: starts with digit (e.g., "1. First Normal Form") 
            is_subsection = re.match(r"^\d+\.\s+\w", line) and not line.endswith(".")
            
            if is_major_heading:
                story.append(Spacer(1, 0.2 * inch))
                story.append(Paragraph(PDFGenerator.sanitize_text(line), PDFGenerator.HEADING_STYLE))
                story.append(Spacer(1, 0.05 * inch))
                i += 1
                continue
            elif is_section_heading:
                story.append(Spacer(1, 0.15 * inch))
                story.append(Paragraph(PDFGenerator.sanitize_text(line), PDFGenerator.SUBHEADING_STYLE))
                story.append(Spacer(1, 0.05 * inch))
                i += 1
                continue
            elif is_subsection:
                story.append(Spacer(1, 0.1 * inch))
                story.append(Paragraph(PDFGenerator.sanitize_text(line), PDFGenerator.SUBHEADING2_STYLE))
                i += 1
                continue
            
            # Detect bullet points or numbered lists (allow up to 2 consecutive items)
            if line.startswith(("- ", "• ", "* ")) or (len(line) > 2 and line[0].isdigit() and line[1] in ".)" and line[2] == " "):
                # Collect consecutive list items
                list_items = []
                list_start = i
                while i < len(lines):
                    curr_line = lines[i].strip()
                    if curr_line and (curr_line.startswith(("- ", "• ", "* ")) or 
                                     (len(curr_line) > 2 and curr_line[0].isdigit() and 
                                      curr_line[1] in ".)" and curr_line[2] == " ")):
                        list_items.append(curr_line)
                        i += 1
                    elif not curr_line:
                        i += 1
                        break
                    else:
                        break
                
                # Format list with reduced spacing
                for item in list_items:
                    list_style = ParagraphStyle(
                        "ListItem",
                        parent=PDFGenerator.BODY_STYLE,
                        leftIndent=20,
                        spaceAfter=6,
                    )
                    story.append(Paragraph(PDFGenerator.sanitize_text(item), list_style))
                continue
            
            # Regular paragraph - collect multi-line paragraphs
            para_lines = [line]
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                # Stop if we hit a heading, list item, or table
                if (next_line and 
                    not next_line.endswith(":") and 
                    not next_line.startswith(("- ", "• ", "* ")) and 
                    not "|" in next_line and
                    not (len(next_line) > 2 and next_line[0].isdigit() and next_line[1] in ".)") and 
                    not (next_line.isupper() and len(next_line) > 5 and next_line.count(" ") >= 1)):  # Don't merge with ALL CAPS headings
                    para_lines.append(next_line)
                    i += 1
                else:
                    break
            
            para_text = " ".join(para_lines)
            if para_text.strip():
                story.append(Paragraph(PDFGenerator.sanitize_text(para_text), PDFGenerator.BODY_STYLE))
        
        return story
    
    @staticmethod
    def _format_metadata(metadata: dict) -> str:
        """Format metadata as HTML for display in PDF."""
        items = []
        
        if "title" in metadata:
            items.append(f"<b>Title:</b> {PDFGenerator.sanitize_text(metadata['title'])}")
        
        if "extraction_info" in metadata:
            info = metadata["extraction_info"]
            if isinstance(info, dict):
                items.append(f"<b>Source:</b> {info.get('filename', 'Unknown')}")
                items.append(f"<b>Format:</b> {info.get('extraction_method', 'Unknown')}")
        
        if "tokens_used" in metadata:
            tokens = metadata["tokens_used"]
            if isinstance(tokens, dict):
                input_tokens = tokens.get("input", 0)
                output_tokens = tokens.get("output", 0)
                items.append(f"<b>Tokens Used:</b> {input_tokens} input, {output_tokens} output")
        
        if "model" in metadata:
            items.append(f"<b>Model:</b> {metadata['model']}")
        
        return "<br/>".join(items)
    
    @staticmethod
    def save_pdf(pdf_bytes: bytes, filepath: str) -> None:
        """Save PDF bytes to file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as f:
            f.write(pdf_bytes)
