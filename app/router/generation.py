# Assuming this code is in app/routers/stream.py or similar

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse # Added JSONResponse for error handling
from google import genai
from google.genai import types
from app.logging_config import logger
from app.config import PROJECT_ID, LOCATION, GEMINI_MODEL

# Assuming LANGUAGE_MAP is defined elsewhere or add it here
# It's better to have this mapping in a shared location like app/utils.py
# For now, adding it here for demonstration
LANGUAGE_MAP = {
    "en": "English",
    "hi": "Hindi",
    "kn": "Kannada",
    "ta": "Tamil",
    "ml": "Malayalam", # Added Malayalam as example
    "bn": "Bengali", # Added Bengali as example
    "gu": "Gujarati", # Added Gujarati as example
    "pa": "Punjabi", # Added Punjabi as example
    "te": "Telugu", # Added Telugu as example
    # Add more languages here to match frontend
}

router = APIRouter()

@router.post("/generate-stream")
async def generate_stream(request: Request):
    """
    Streams generated text from Gemini based on user input, diagnosis context,
    and the specified language.
    """
    try:
        body = await request.json()
        user_input = body.get("input", "") # This contains context + user question
        language = body.get("language", "en") # Get language, default to 'en'

        # Validate and get language name for prompt
        lang_name = LANGUAGE_MAP.get(language, "English")

        # Append language instruction to the prompt
        # The frontend sends "Previous diagnosis/response context: '...'. User asks: '...'"
        # We add the language instruction to *that* combined string.
        prompt_text = f"{user_input}\n\nRespond in {lang_name}."

        logger.info(f"Generating stream response for language: {lang_name} ({language}). Prompt: {prompt_text[:100]}...")

        async def stream_response_chunks():
            """Async generator function to yield text chunks."""
            try:
                client = genai.Client(
                    vertexai=True,
                    project=PROJECT_ID,
                    location=LOCATION,
                )

                contents = [
                    types.Content(
                        role="user",
                        parts=[types.Part(text=prompt_text)] # Use the language-instructed prompt
                    )
                ]

                # Use the same generate_content_config as before
                generate_content_config = types.GenerateContentConfig(
                    temperature=1, # Be mindful of high temperature for technical info
                    top_p=0.95,
                    max_output_tokens=65535,
                    response_modalities=["TEXT"],
                    system_instruction=[ # Keep system instruction language-agnostic
                        types.Part.from_text(text="""
You are a helpful AI assistant providing information about plant health.
Answer the user's question based on the provided context about the plant diagnosis.
Be concise and relevant to the user's query.
""")
                    ]
                )

                # Use generate_content_stream for chunked response
                stream = client.models.generate_content_stream(
                    model=GEMINI_MODEL,
                    contents=contents,
                    config=generate_content_config,
                )

                for chunk in stream:
                    if chunk.text:
                        # logger.debug(f"Streaming chunk: {chunk.text[:50]}...") # Optional: log chunks
                        yield chunk.text

            except Exception as e:
                # If an error occurs *during* streaming, yield an error chunk
                error_msg = f"\n[ERROR] Failed to stream response: {str(e)}"
                logger.error(f"Generation stream error: {e}", exc_info=True)
                yield error_msg # Yield the error message as the last chunk

        # Return the async generator as a StreamingResponse
        return StreamingResponse(stream_response_chunks(), media_type="text/plain")

    except Exception as e:
        # If an error occurs *before* streaming starts (e.g., parsing JSON body)
        logger.error(f"Error setting up stream: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": f"Internal server error: {e}"})