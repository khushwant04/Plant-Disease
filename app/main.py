# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.router import analyse, pdf_report, prediction, generation
from app.models.model_loader import model_manager
from app.logging_config import logger
from app.config import ORIGINS

# Initialize FastAPI app
app = FastAPI(title="Plant Disease API", 
              description="API for plant disease prediction and AI assistance",
              version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(prediction.router, tags=["prediction"])
app.include_router(generation.router, tags=["generation"])
app.include_router(analyse.router, tags=["Analysis"])
app.include_router(pdf_report.router, tags=["Analysis"])

@app.on_event("startup")
async def startup_event():
    """Load the model during startup"""
    logger.info("Starting up the application...")
    # Load the model at startup
    model_manager.load_model()
    logger.info("Application started successfully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
