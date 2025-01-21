from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import easyocr
import PyPDF2
from pydantic import BaseModel
from typing import List
import io
from PIL import Image
import logging
from textblob import TextBlob  # Ensure the textblob library is installed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

# Initialize FastAPI app
app = FastAPI(title="Document Processor and Analyzer API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Update this to your frontend's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OCR Reader
reader = easyocr.Reader(["en"])

# Define response models
class ExtractedText(BaseModel):
    text: str
    page_number: int
    confidence: float

class SentimentResult(BaseModel):
    text: str
    sentiment: str
    confidence: float

class AnalysisResponse(BaseModel):
    status: str
    pages: List[ExtractedText]
    results: List[SentimentResult]
    suggestions: List[str]
    file_type: str

class ProcessingResponse(BaseModel):
    status: str
    pages: List[ExtractedText]
    file_type: str

# Utility functions
def process_pdf(file_bytes: bytes) -> List[ExtractedText]:
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        pages = []
        for page_num, page in enumerate(pdf_reader.pages):
            text = page.extract_text()
            pages.append(ExtractedText(
                text=text or "No text found",
                page_number=page_num + 1,
                confidence=1.0 if text else 0.0
            ))
        return pages
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail="Error processing PDF")

def process_image(image_bytes: bytes) -> List[ExtractedText]:
    try:
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode != "RGB":
            image = image.convert("RGB")

        result = reader.readtext(image_bytes, detail=1)
        pages = [
            ExtractedText(
                text=item[1],
                page_number=1,
                confidence=float(item[2])
            )
            for item in result
        ]
        return pages or [ExtractedText(text="No text found", page_number=1, confidence=0.0)]
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise HTTPException(status_code=500, detail="Error processing image")

def generate_suggestions(content: str) -> List[str]:
    suggestions = []
    words = content.split()

    # Suggest hashtags if not present
    if "#" not in content:
        suggestions.append("Add hashtags to increase visibility, e.g., #Trending #YourTopic.")

    # Suggest adding a call-to-action
    if not any(phrase in content.lower() for phrase in ["click", "check out", "buy now", "learn more"]):
        suggestions.append("Include a call-to-action, e.g., 'Learn more at the link in our bio.'")

    # Suggest adding emojis if none exist
    emojis = "😀😂🎉👍🔥"
    if not any(char in content for char in emojis):
        suggestions.append("Include emojis to make your content visually appealing and fun.")

    # Suggest simplifying lengthy content
    if len(words) > 100:
        suggestions.append("Your content is lengthy. Simplify it to retain reader attention.")

    # Sentiment-based suggestions
    blob = TextBlob(content)
    sentiment = blob.sentiment.polarity
    if sentiment < 0:
        suggestions.append("Rephrase negative statements to sound more positive.")
    elif sentiment == 0:
        suggestions.append("Add more expressive language to make your content engaging.")

    # Suggest visuals if mentioning products/services
    if any(keyword in content.lower() for keyword in ["product", "service", "offer", "sale"]):
        suggestions.append("Include visuals like images or videos to showcase your products or services.")

    # Suggest audience targeting
    if "everyone" in content.lower() or "anyone" in content.lower():
        suggestions.append("Make your content specific to a target audience for better engagement.")

    # Suggest optimal posting times based on greetings
    if "morning" in content.lower():
        suggestions.append("Post this in the morning hours for better engagement.")
    elif "evening" in content.lower():
        suggestions.append("Consider posting this in the evening for higher visibility.")

    # Suggest adding links
    if "http" not in content and "www" not in content:
        suggestions.append("Add a link to direct users to your website or product.")

    return suggestions

@app.post("/process-document", response_model=ProcessingResponse)
async def process_document(file: UploadFile = File(...)):
    try:
        content = await file.read()
        file_type = file.content_type
        logger.info(f"Processing file: {file.filename}, Type: {file_type}, Size: {len(content)} bytes")

        if file_type == "application/pdf":
            pages = process_pdf(content)
            return ProcessingResponse(status="success", pages=pages, file_type="pdf")
        elif file_type.startswith("image/"):
            pages = process_image(content)
            return ProcessingResponse(status="success", pages=pages, file_type="image")
        else:
            logger.error(f"Unsupported file type: {file_type}")
            raise HTTPException(status_code=400, detail="Unsupported file type")
    except HTTPException as e:
        logger.error(f"HTTP Exception: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# API route for content analysis
@app.post("/analyze-content", response_model=AnalysisResponse)
async def analyze_content(file: UploadFile = File(...)):
    try:
        content = await file.read()
        file_type = file.content_type
        logger.info(f"Processing file: {file.filename}, Type: {file_type}, Size: {len(content)} bytes")

        if file_type == "application/pdf":
            pages = process_pdf(content)
        elif file_type.startswith("image/"):
            pages = process_image(content)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # Combine all extracted text
        full_text = " ".join(page.text for page in pages)

        # Analyze text and generate suggestions
        suggestions = generate_suggestions(full_text)

        return AnalysisResponse(
            status="success",
            pages=pages,
            results=[SentimentResult(text=full_text, sentiment="analyzed", confidence=1.0)],
            suggestions=suggestions,
            file_type=file_type
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
