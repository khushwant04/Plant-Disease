# app/routers/generation.py
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from google import genai
from google.genai import types
from app.logging_config import logger
from app.config import PROJECT_ID, LOCATION, GEMINI_MODEL

router = APIRouter()

@router.post("/generate-stream")
async def generate_stream(request: Request):
    body = await request.json()
    user_input = body.get("input", "")
    
    logger.info(f"Generating response for input: {user_input[:50]}...")

    def stream_response():
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location=LOCATION,
        )

        contents = [
            types.Content(
                role="user",
                parts=[types.Part(text=user_input)]
            )
        ]
        
        generate_content_config = types.GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            max_output_tokens=8192,
            response_modalities=["TEXT"],
        )

        try:
            for chunk in client.models.generate_content_stream(
                model=GEMINI_MODEL,
                contents=contents,
                config=generate_content_config,
            ):
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            error_msg = f"\n[ERROR] {str(e)}"
            logger.error(f"Generation error: {e}")
            yield error_msg

    return StreamingResponse(stream_response(), media_type="text/plain")
