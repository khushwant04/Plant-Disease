# app/routers/analysis.py

from fastapi import APIRouter, File, UploadFile, Form, Body # Import Form and Body
from fastapi.responses import JSONResponse, StreamingResponse # StreamingResponse for generate-stream
from PIL import Image
import torch
import io
import json # Import json for streaming

from app.models.model_loader import model_manager
from app.utils import preprocess_image # Assuming preprocess_image is in app.utils
from app.logging_config import logger
from app.config import PREDICTION_THRESHOLD, PROJECT_ID, LOCATION, GEMINI_MODEL

from google import genai
from google.genai import types

# --- Language Mapping ---
# Map language codes (from frontend) to names suitable for Gemini prompt
LANGUAGE_MAP = {
    "en": "English",
    "hi": "Hindi",
    "kn": "Kannada",
    "ta": "Tamil",
    # Add other languages here
    "ml": "Malayalam",
    "bn": "Bengali",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "te": "Telugu",
}

router = APIRouter()

@router.post("/analyze/")
async def analyze_image(
    file: UploadFile = File(...),
    language: str = Form(default="en") # Accept language as form data
):
    """
    Analyzes an uploaded plant image and generates a diagnosis in the specified language.
    """
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = model_manager.get_model()
    idx_to_class = model_manager.get_idx_to_class()

    # Validate and get language name, default to English if invalid
    lang_name = LANGUAGE_MAP.get(language, "English")
    logger.info(f"Processing analysis request in language: {lang_name} ({language})")


    try:
        # Step 1: Prediction
        image_bytes = await file.read() # Read the file bytes once
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_tensor = preprocess_image(image).to(device)

        with torch.no_grad():
            output = model(image_tensor)

        scores = torch.softmax(output, dim=1)
        max_score, predicted = torch.max(scores, 1)

        if max_score.item() > PREDICTION_THRESHOLD:
            class_index = predicted.item()
            class_name = idx_to_class[class_index]
        else:
            class_index = None
            class_name = "Healthy image" # Keep this key name consistent internally

        logger.info(f"Predicted: {class_name} with confidence {max_score.item()}")

        # Step 2: Construct Gemini Query including language instruction
        # The disease name (class_name) is in English from the model's labels.
        # We instruct Gemini to explain *about* this disease in the target language.
        if class_name == "Healthy image":
             query_text = (
                 f"Provide detailed tips on maintaining plant health and preventing common diseases. "
                 f"Respond in {lang_name}."
             )
        else:
            query_text = (
                f"Give me detailed information about the plant disease '{class_name}', "
                f"including causes, symptoms, preventive measures, and treatments. "
                f"Respond in {lang_name}." # Add language instruction here
            )
        logger.info(f"Gemini Query: {query_text[:100]}...") # Log truncated query


        # Step 3: Gemini Generation
        # Configure Gemini client - ensure this is correctly initialized
        # (Your existing initialization seems fine, assuming project_id and location are set in config)
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location=LOCATION,
        )

        contents = [types.Content(role="user", parts=[types.Part(text=query_text)])]

        generate_content_config = types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.9,
            max_output_tokens=65535,
            response_modalities=["TEXT"],
            # System instruction remains language-agnostic, user query specifies language
            system_instruction=[
                types.Part.from_text(text="""
You are a knowledgeable plant pathology assistant designed to provide detailed, accurate, and practical information about plant diseases.
Your goal is to educate users about plant health by explaining:
1. Disease Overview
2. Causes
3. Symptoms
4. Prevention
5. Treatment & Control
6. Impact

Always be factual, up-to-date with agricultural practices, and provide advice that is relevant for field application. Avoid speculation.
""")
            ]
        )

        gemini_response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=generate_content_config,
            # Adding language instruction directly in the prompt text is the primary method.
            # There isn't a standard API parameter for response language across all LLMs.
        )

        # Extract text from response
        generated_text = ""
        if hasattr(gemini_response, 'text'):
             generated_text = gemini_response.text
        elif gemini_response.candidates and gemini_response.candidates[0].content.parts:
             generated_text = "".join(part.text for part in gemini_response.candidates[0].content.parts if hasattr(part, 'text'))

        if not generated_text:
             logger.warning("Gemini generated no text response.")
             generated_text = f"Could not generate response for {class_name}. Please try again or ask a follow-up question." # Fallback

        return JSONResponse(content={
            "prediction": {
                "class_index": class_index,
                "class_name": class_name, # Keep the English class name for consistency/internal use
                "confidence": float(max_score.item())
            },
            "gemini_response": generated_text # This text should now be in the target language
        })

    except Exception as e:
        logger.error(f"Error in analysis endpoint: {e}", exc_info=True) # Log traceback
        return JSONResponse(status_code=500, content={"error": f"Internal server error during analysis: {e}"})


# Define a Pydantic model for the streaming request body
# Assuming your backend might use Pydantic models, create one if you don't have it
# If not using Pydantic, you can accept the body as a dict like body: dict = Body(...)
from pydantic import BaseModel

class StreamRequest(BaseModel):
    input: str # This will be the combined prompt from frontend
    language: str = "en" # Add language parameter

@router.post("/generate-stream")
async def generate_stream(request: StreamRequest): # Use the Pydantic model
    """
    Streams generated text from Gemini based on user input and diagnosis context
    in the specified language.
    """
    user_input = request.input # This already includes context + user question from frontend
    language = request.language

    # Validate and get language name
    lang_name = LANGUAGE_MAP.get(language, "English")
    logger.info(f"Processing stream request in language: {lang_name} ({language})")

    # --- Construct Gemini Query including language instruction ---
    # Modify the input sent to Gemini to explicitly request the response language.
    # The frontend sends input like "Based on this plant diagnosis: [English context]. The user now asks: [User's question]"
    # We append the language instruction to this.
    query_text = f"{user_input}\n\nRespond in {lang_name}."
    logger.info(f"Gemini Stream Query: {query_text[:100]}...") # Log truncated query


    try:
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location=LOCATION,
        )

        contents = [types.Content(role="user", parts=[types.Part(text=query_text)])]

        generate_content_config = types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.9,
            max_output_tokens=65535,
            response_modalities=["TEXT"],
            # System instruction remains language-agnostic
            system_instruction=[
                 types.Part.from_text(text="""
You are a helpful AI assistant providing information about plant health.
Answer the user's question based on the provided context about the plant diagnosis.
Be concise and relevant to the user's query.
""")
            ]
        )

        # Use generate_content with stream=True
        # Note: Vertex AI's Python client streaming works differently than the public API.
        # You get a generator object that yields Response objects.
        # We need to iterate through these and extract text parts.
        # The stream=True parameter is part of the generate_content call for Vertex AI.
        stream_response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=generate_content_config,
            stream=True # Enable streaming
        )

        async def generate_text_chunks():
            """Generator function to yield text chunks from the streaming response."""
            try:
                for response in stream_response:
                    if response.candidates:
                         # Concatenate text from all parts in the candidate's content
                         chunk = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
                         if chunk:
                            #logger.debug(f"Streaming chunk: {chunk[:50]}...") # Optional: log chunks
                            yield chunk
            except Exception as e:
                 logger.error(f"Error during streaming response: {e}", exc_info=True)
                 yield f"Error: Failed to stream response. {str(e)}" # Yield error to frontend


        # Return StreamingResponse
        # media_type="text/plain" is suitable for simple text streaming
        # For more complex interactions (like SSE), you might need "text/event-stream"
        return StreamingResponse(generate_text_chunks(), media_type="text/plain")


    except Exception as e:
        logger.error(f"Error in generate-stream endpoint: {e}", exc_info=True)
        # For streaming, a single error response isn't ideal after the stream starts.
        # If the error occurs before the first chunk, returning JSON is okay.
        # If it occurs mid-stream, the generator needs to yield the error.
        # The generator handles mid-stream errors, so this outer catch is for errors
        # occurring before the generator starts (e.g., client connection failed).
        return JSONResponse(status_code=500, content={"error": f"Internal server error during streaming setup: {e}"})
