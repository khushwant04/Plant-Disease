# Assuming this code is in app/routers/pdf.py or similar

from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse, JSONResponse
from io import BytesIO
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer, SimpleDocTemplate
# Add font registration if needed for non-Latin scripts
# from reportlab.pdfbase import pdfmetrics
# from reportlab.pdfbase.ttfonts import TTFont

from google import genai
from google.genai import types
from app.config import PROJECT_ID, LOCATION, GEMINI_MODEL
from app.logging_config import logger

# Assuming LANGUAGE_MAP is defined elsewhere or add it here
# It's better to have this mapping in a shared location like app/utils.py
# For now, adding it here for demonstration
LANGUAGE_MAP = {
    "en": "English",
    "hi": "Hindi",
    "kn": "Kannada",
    "ta": "Tamil",
    "ml": "Malayalam",
    "bn": "Bengali",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "te": "Telugu",
    # Add more languages here
}

# --- Optional: Font Registration for reportlab ---
# This is CRUCIAL if you want to render non-Latin scripts correctly in the PDF.
# You need to acquire TrueType font files (.ttf) that support these scripts.
# Example (you'd need actual font files and paths):
# try:
#     pdfmetrics.registerFont(TTFont('NirmalaUI', 'path/to/NirmalaUI.ttf')) # Common font supporting many Indian scripts
#     # Or register separate fonts like Hindi, Kannada, Tamil specific ones
#     # pdfmetrics.registerFont(TTFont('ArialUnicodeMS', 'path/to/Arial Unicode MS.ttf')) # Large Unicode font
#     # You'd then use these font names in your ParagraphStyles
#     logger.info("Registered custom fonts for PDF generation.")
# except Exception as e:
#     logger.warning(f"Could not register fonts for PDF: {e}. Non-Latin characters may not render.")

router = APIRouter()

# Define a Pydantic model for the request body
from pydantic import BaseModel

class PDFReportRequest(BaseModel):
    messages: list[dict]
    language: str = "en" # Add language parameter to the model

@router.post("/generate-pdf/")
async def generate_pdf_report(request: PDFReportRequest): # Use the Pydantic model
    """
    1) Generate a detailed summarized report via Gemini based on chat transcript and language.
    2) Render the summary into a well-formatted PDF.
    """
    messages = request.messages
    language = request.language

    # Validate and get language name for prompt
    lang_name = LANGUAGE_MAP.get(language, "English")
    logger.info(f"Generating PDF report in language: {lang_name} ({language})")

    try:
        # 1) Build detailed report generation prompt
        # The transcript itself might contain mixed languages if the user typed
        # in a local language for follow-ups, but the bot's analysis *should*
        # now be in the target language.
        transcript = "\n\n".join(f"{m['from'].upper()}: {m['text']}" for m in messages)

        # Modify the prompt to instruct Gemini to generate the REPORT in the target language
        report_prompt = (
            "You are a professional agricultural report generator. "
            "Based on the following chat transcript, create a comprehensive, detailed report "
            "with proper markdown formatting. Ensure the report is written entirely in {lang_name}.\n\n" # <<< Add language instruction here
            "Include the following sections:\n\n"
            "## Plant Health Assessment\n"
            "## Diagnosis Details\n"
            "## Causes and Contributing Factors\n"
            "## Treatment Recommendations\n"
            "## Preventive Measures\n"
            "## Additional Notes\n\n"
            "Use proper markdown formatting including headers (##, ###), bullet points, emphasis (*italic*), "
            "strong (**bold**), and any other markdown elements that would improve readability. "
            "DO NOT include any mention that this is based on a chat transcript."
            "Translate any necessary disease names or technical terms accurately." # <<< Added instruction
            f"\n\n{transcript}" # Append transcript last
        ).format(lang_name=lang_name) # Format the language name into the prompt

        logger.info(f"Gemini PDF Prompt: {report_prompt[:100]}...") # Log truncated prompt


        # 2) Ask Gemini for the detailed report
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location=LOCATION,
        )
        contents = [types.Content(role="user", parts=[types.Part(text=report_prompt)])]
        config = types.GenerateContentConfig(
            temperature=0.2, # Lower temp for structured output
            top_p=0.9,
            max_output_tokens=65535,
            response_modalities=["TEXT"]
        )
        gem_response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=config
        )
        # Extract text from response
        report_text = ""
        if hasattr(gem_response, 'text'):
             report_text = gem_response.text
        elif gem_response.candidates and gem_response.candidates[0].content.parts:
             report_text = "".join(part.text for part in gem_response.candidates[0].content.parts if hasattr(part, 'text'))

        if not report_text:
             logger.warning("Gemini generated no text for the PDF report.")
             report_text = "Could not generate the report content. Please try again." # Fallback

        # 3) Create PDF in memory with better formatting
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)

        styles = getSampleStyleSheet()

        # Define or update styles safely - make sure fonts are registered if needed
        def add_or_update_style(name, **kwargs):
            if name in styles:
                for key, value in kwargs.items():
                    setattr(styles[name], key, value)
            else:
                styles.add(ParagraphStyle(name=name, **kwargs))

        # Set up or update our styles
        # NOTE: If using custom fonts (like NirmalaUI), you need to register them
        # above and use their names here (e.g., fontName='NirmalaUI')
        add_or_update_style('Title',
                        fontName='Helvetica-Bold', # Consider 'NirmalaUI-Bold' if available & registered
                        fontSize=18,
                        spaceAfter=16,
                        alignment=1) # Center align title

        add_or_update_style('Heading2',
                        fontName='Helvetica-Bold', # Consider 'NirmalaUI-Bold'
                        fontSize=14,
                        spaceAfter=10,
                        leading=16) # Added leading

        add_or_update_style('Heading3',
                        fontName='Helvetica-Bold', # Consider 'NirmalaUI-Bold'
                        fontSize=12,
                        spaceAfter=8,
                        leading=14) # Added leading

        add_or_update_style('BodyText',
                        fontName='Helvetica', # Consider 'NirmalaUI' or another Unicode font
                        fontSize=11,
                        leading=14,
                        spaceAfter=6)

        # Process markdown to PDF elements
        elements = []

        # Add title - this is static text, potentially needs translation
        # For simplicity, keeping English title. For full translation, you'd need
        # translated titles or another AI call.
        elements.append(Paragraph("PlantAI Detailed Assessment Report", styles['Title']))
        elements.append(Spacer(1, 12))

        # Safely process markdown - This strip HTML and basic markdown.
        # For complex scripts, reportlab needs the right font and potentially complex text layout.
        def safe_text_processing(text):
            """Strip HTML tags and basic markdown, suitable for reportlab's basic text handling."""
            # First strip any existing HTML tags
            text = re.sub(r'<[^>]*>', '', text)

            # Then safely replace markdown with plain text equivalents
            # This might not perfectly handle nested markdown or specific edge cases,
            # but provides a cleaner input for Paragraph.
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', text) # Bold **text** -> text
            text = re.sub(r'\*(.+?)\*', r'\1', text)     # Italic *text* -> text
            text = re.sub(r'^- ', '• ', text, flags=re.M) # Bullet points - -> •
            text = text.replace('&', '&').replace('<', '<').replace('>', '>') # Escape XML entities for ReportLab

            return text

        # Process the report text section by section
        # This logic assumes Gemini *follows* the markdown section headers.
        current_section = None
        section_content_lines = [] # Store lines for a section before adding as a paragraph

        lines = report_text.strip().split('\n') # Process line by line
        for i, line in enumerate(lines):
            line = line.strip()

            # Check for new section header (H2)
            if line.startswith('## '):
                # Process the content collected for the previous section
                if section_content_lines:
                    section_text = "\n".join(section_content_lines).strip()
                    if section_text:
                         # Use safe_text_processing before creating Paragraph
                        elements.append(Paragraph(safe_text_processing(section_text), styles['BodyText']))
                    section_content_lines = [] # Reset for the new section

                # Add the new section header
                current_section_title = line[3:].strip()
                if current_section_title:
                     elements.append(Paragraph(safe_text_processing(current_section_title), styles['Heading2']))
                     elements.append(Spacer(1, 5)) # Small space after header

            # Check for subheading header (H3)
            elif line.startswith('### '):
                 # Process content before subheading (if any)
                 if section_content_lines:
                    section_text = "\n".join(section_content_lines).strip()
                    if section_text:
                         elements.append(Paragraph(safe_text_processing(section_text), styles['BodyText']))
                    section_content_lines = [] # Reset

                 # Add the subheading
                 subheading_title = line[4:].strip()
                 if subheading_title:
                     elements.append(Paragraph(safe_text_processing(subheading_title), styles['Heading3']))
                     elements.append(Spacer(1, 3)) # Small space after subheading

            # Check for list items (basic handling)
            elif line.startswith('- ') or line.startswith('* '):
                 # Process content before list item
                 if section_content_lines:
                    section_text = "\n".join(section_content_lines).strip()
                    if section_text:
                         elements.append(Paragraph(safe_text_processing(section_text), styles['BodyText']))
                    section_content_lines = [] # Reset

                 # Add the list item as a paragraph
                 list_item_text = line[2:].strip()
                 if list_item_text:
                     # Add a bullet character; use a slightly indented style if defined
                     elements.append(Paragraph(safe_text_processing('•  ' + list_item_text), styles['BodyText'])) # Use BodyText for now

            elif not line and section_content_lines:
                 # Handle empty lines separating paragraphs within a section
                 section_text = "\n".join(section_content_lines).strip()
                 if section_text:
                      elements.append(Paragraph(safe_text_processing(section_text), styles['BodyText']))
                 section_content_lines = []
                 elements.append(Spacer(1, 6)) # Space between paragraphs


            else:
                # Regular text lines, add to current section content buffer
                # Only add if there's a current section or if it's text before the first section
                 if current_section is not None or line: # Collect text even before the first header
                     section_content_lines.append(line)


        # Add any remaining content after the last section header
        if section_content_lines:
             section_text = "\n".join(section_content_lines).strip()
             if section_text:
                 elements.append(Paragraph(safe_text_processing(section_text), styles['BodyText']))


        # Build the document
        doc.build(elements)
        buffer.seek(0)

        return StreamingResponse(buffer, media_type="application/pdf",
                                headers={"Content-Disposition":"attachment; filename=PlantAI_Report.pdf"})
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error generating PDF report: {e}", exc_info=True) # Log traceback
        return JSONResponse(status_code=500, content={"error": f"Failed to generate PDF: {str(e)}", "details": "Check server logs for more information"})