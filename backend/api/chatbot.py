from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter()


class ChatbotRequest(BaseModel):
    question: str


@router.post("/chat")
def chat(req: ChatbotRequest):
    question = (req.question or "").lower()
    # Very simple rules-based stub
    if "acne" in question:
        answer = "For acne-prone skin, use a gentle cleanser and salicylic acid."
    elif "hydrate" in question or "dry" in question:
        answer = "Hydration: look for hyaluronic acid serums and ceramide moisturizers."
    else:
        answer = "Try a basic routine: cleanse, moisturize, and SPF in the morning."
    return {"answer": answer}


