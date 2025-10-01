from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime
from collections import defaultdict
import uuid
import re


router = APIRouter()


# ============= Models =============

class ConversationState(str, Enum):
    GREETING = "greeting"
    SKIN_TYPE = "skin_type"
    CONCERNS = "concerns"
    AGE_RANGE = "age_range"
    ROUTINE = "routine"
    LIFESTYLE = "lifestyle"
    BUDGET = "budget"
    ALLERGIES = "allergies"
    ANALYSIS = "analysis"
    RECOMMENDATION = "recommendation"
    FOLLOWUP = "followup"


class SkinProfile(BaseModel):
    skin_type: Optional[str] = None
    concerns: List[str] = Field(default_factory=list)
    age_range: Optional[str] = None
    current_routine: List[str] = Field(default_factory=list)
    lifestyle: Dict[str, Any] = Field(default_factory=dict)
    budget: Optional[str] = None
    allergies: List[str] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    state: ConversationState = ConversationState.GREETING
    profile: SkinProfile = Field(default_factory=SkinProfile)
    messages: List[ChatMessage] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[Dict] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: Optional[str] = None
    question: Optional[str] = None  # backward compatibility with older frontend
    session_id: Optional[str] = None
    image_path: Optional[str] = None  # Allow referencing uploaded images
    
    @property
    def user_message(self) -> str:
        """Get the user message from either message or question field"""
        return self.message or self.question or ""


class ChatResponse(BaseModel):
    response: str
    session_id: str
    state: str
    suggestions: List[str] = Field(default_factory=list)
    products: List[Dict] = Field(default_factory=list)
    requires_image: bool = False
    profile_complete: bool = False
    error: Optional[str] = None  # Field to communicate errors to frontend


# ============= Chatbot Engine =============

class SkincareChatbot:
    """Advanced skincare consultation chatbot"""

    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
        self.question_flow = self._initialize_question_flow()
        self.nlp_patterns = self._initialize_nlp_patterns()

    def _initialize_question_flow(self) -> Dict:
        """Define the conversation flow and questions"""
        return {
            ConversationState.GREETING: {
                "questions": [
                    "👋 Hi! I'm your personal skincare consultant. I'll help you build the perfect routine. What's your name?",
                    "Hello! I'm here to help you achieve your best skin. May I know your name?",
                ],
                "next": ConversationState.SKIN_TYPE,
            },
            ConversationState.SKIN_TYPE: {
                "questions": [
                    "Nice to meet you! Let's start with the basics. How would you describe your skin type?\n\n• **Oily** - Shiny, prone to breakouts\n• **Dry** - Flaky, tight feeling\n• **Combination** - Oily T-zone, dry cheeks\n• **Normal** - Balanced\n• **Sensitive** - Easily irritated",
                ],
                "validators": ["oily", "dry", "combination", "normal", "sensitive"],
                "next": ConversationState.CONCERNS,
            },
            ConversationState.CONCERNS: {
                "questions": [
                    "What are your main skin concerns? (You can mention multiple)\n\n• Acne & breakouts\n• Fine lines & wrinkles\n• Dark spots & hyperpigmentation\n• Large pores\n• Redness & rosacea\n• Dullness\n• Dark circles\n• Uneven texture",
                ],
                "multi_select": True,
                "next": ConversationState.AGE_RANGE,
            },
            ConversationState.AGE_RANGE: {
                "questions": [
                    "Which age group do you belong to? This helps me recommend age-appropriate products.\n\n• Under 20\n• 20-30\n• 30-40\n• 40-50\n• 50+",
                ],
                "next": ConversationState.ROUTINE,
            },
            ConversationState.ROUTINE: {
                "questions": [
                    "Tell me about your current skincare routine. What products do you use daily? (cleanser, moisturizer, serum, etc.)",
                ],
                "next": ConversationState.LIFESTYLE,
            },
            ConversationState.LIFESTYLE: {
                "questions": [
                    "Let's talk about your lifestyle:\n\n• How many hours of sleep do you usually get?\n• Do you wear makeup daily?\n• How much water do you drink?\n• Do you spend a lot of time outdoors?",
                ],
                "next": ConversationState.BUDGET,
            },
            ConversationState.BUDGET: {
                "questions": [
                    "What's your monthly skincare budget?\n\n• **Budget-friendly** (Under $50)\n• **Mid-range** ($50-150)\n• **Premium** ($150-300)\n• **Luxury** ($300+)",
                ],
                "next": ConversationState.ALLERGIES,
            },
            ConversationState.ALLERGIES: {
                "questions": [
                    "Do you have any allergies or ingredients you want to avoid? (e.g., fragrances, essential oils, retinol)",
                ],
                "next": ConversationState.ANALYSIS,
            },
        }

    def _initialize_nlp_patterns(self) -> Dict:
        """Initialize NLP patterns for understanding user input"""
        return {
            "skin_types": {
                "oily": ["oily", "greasy", "shiny", "sebum"],
                "dry": ["dry", "flaky", "dehydrated", "tight"],
                "combination": ["combination", "mixed", "combo", "t-zone"],
                "normal": ["normal", "balanced", "regular"],
                "sensitive": ["sensitive", "reactive", "irritated", "red"],
            },
            "concerns": {
                "acne": ["acne", "pimples", "breakouts", "zits", "blackheads", "whiteheads"],
                "aging": ["wrinkles", "fine lines", "aging", "anti-aging", "crow's feet"],
                "pigmentation": ["dark spots", "hyperpigmentation", "melasma", "sun spots", "age spots"],
                "pores": ["large pores", "pores", "enlarged pores", "visible pores"],
                "redness": ["redness", "rosacea", "inflammation", "irritation"],
                "dullness": ["dull", "dullness", "lackluster", "tired skin"],
                "dark_circles": ["dark circles", "under eye", "eye bags", "puffy eyes"],
                "texture": ["texture", "rough", "bumpy", "uneven"],
            },
            "products": {
                "cleanser": ["cleanser", "wash", "cleansing", "face wash"],
                "moisturizer": ["moisturizer", "cream", "lotion", "hydrator"],
                "serum": ["serum", "treatment", "essence", "ampoule"],
                "sunscreen": ["sunscreen", "spf", "sun protection", "sunblock"],
                "toner": ["toner", "tonic", "astringent"],
                "exfoliant": ["exfoliant", "scrub", "peel", "aha", "bha"],
                "mask": ["mask", "face mask", "sheet mask"],
                "eye_cream": ["eye cream", "eye serum", "eye treatment"],
            },
            "ingredients": {
                "actives": {
                    "retinol": ["retinol", "retinoid", "retin-a", "tretinoin"],
                    "vitamin_c": ["vitamin c", "ascorbic acid", "l-ascorbic"],
                    "niacinamide": ["niacinamide", "vitamin b3"],
                    "hyaluronic": ["hyaluronic acid", "ha", "sodium hyaluronate"],
                    "salicylic": ["salicylic acid", "bha", "beta hydroxy"],
                    "glycolic": ["glycolic acid", "aha", "alpha hydroxy"],
                }
            },
        }

    def get_or_create_session(self, session_id: Optional[str] = None) -> ChatSession:
        """Get existing session or create new one"""
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]
        new_session = ChatSession()
        self.sessions[new_session.session_id] = new_session
        return new_session

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from user input using NLP patterns"""
        text_lower = text.lower()
        entities = defaultdict(list)

        for skin_type, patterns in self.nlp_patterns["skin_types"].items():
            if any(pattern in text_lower for pattern in patterns):
                entities["skin_type"].append(skin_type)

        for concern, patterns in self.nlp_patterns["concerns"].items():
            if any(pattern in text_lower for pattern in patterns):
                entities["concerns"].append(concern)

        for product, patterns in self.nlp_patterns["products"].items():
            if any(pattern in text_lower for pattern in patterns):
                entities["products"].append(product)

        age_patterns = [
            (r"\b(\d{1,2})\s*years?\s*old\b", "age"),
            (r"\b(\d{1,2})\s*y/?o\b", "age"),
            (r"\bunder\s*(\d{2})\b", "age_under"),
            (r"\b(\d{2})-(\d{2})\b", "age_range"),
            (r"\b(\d{2})s\b", "age_decade"),
        ]
        for pattern, entity_type in age_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                entities[entity_type].extend(matches)

        return dict(entities)

    def update_profile(self, session: ChatSession, entities: Dict[str, List[str]]):
        """Update user profile based on extracted entities"""
        if "skin_type" in entities and entities["skin_type"]:
            session.profile.skin_type = entities["skin_type"][0]
        if "concerns" in entities:
            session.profile.concerns.extend(entities["concerns"])
            session.profile.concerns = list(set(session.profile.concerns))
        if "products" in entities:
            session.profile.current_routine.extend(entities["products"])
            session.profile.current_routine = list(set(session.profile.current_routine))
        if "age" in entities or "age_range" in entities:
            if "age" in entities:
                age = int(entities["age"][0])
                if age < 20:
                    session.profile.age_range = "under_20"
                elif age < 30:
                    session.profile.age_range = "20-30"
                elif age < 40:
                    session.profile.age_range = "30-40"
                elif age < 50:
                    session.profile.age_range = "40-50"
                else:
                    session.profile.age_range = "50+"

    def _get_weekly_treatments(self, profile: SkinProfile) -> List[Dict]:
        treatments = []
        if profile.skin_type == "oily" or "pores" in profile.concerns:
            treatments.append({
                "treatment": "Clay mask",
                "frequency": "1-2 times per week",
                "benefits": "Deep cleansing and pore minimizing",
            })
        if profile.skin_type == "dry" or "dehydration" in profile.concerns:
            treatments.append({
                "treatment": "Hydrating mask",
                "frequency": "2-3 times per week",
                "benefits": "Intense hydration boost",
            })
        if "texture" in profile.concerns or "dullness" in profile.concerns:
            treatments.append({
                "treatment": "Chemical exfoliant",
                "frequency": "1-2 times per week",
                "ingredients": ["AHA (glycolic/lactic acid)"],
                "benefits": "Smooth texture and brighten skin",
            })
        return treatments

    def generate_recommendations(self, profile: SkinProfile) -> Dict:
        recommendations: Dict[str, Any] = {}
        morning_routine: List[Dict[str, Any]] = []
        if profile.skin_type == "oily":
            morning_routine.append({
                "step": 1,
                "product_type": "Cleanser",
                "recommendation": "Gel or foaming cleanser with salicylic acid",
                "ingredients": ["salicylic acid", "tea tree", "niacinamide"],
                "avoid": ["heavy oils", "comedogenic ingredients"],
            })
        elif profile.skin_type == "dry":
            morning_routine.append({
                "step": 1,
                "product_type": "Cleanser",
                "recommendation": "Cream or milk cleanser",
                "ingredients": ["ceramides", "hyaluronic acid", "glycerin"],
                "avoid": ["sulfates", "alcohol"],
            })
        else:
            morning_routine.append({
                "step": 1,
                "product_type": "Cleanser",
                "recommendation": "Gentle gel cleanser",
                "ingredients": ["gentle surfactants", "antioxidants"],
                "avoid": ["harsh sulfates"],
            })

        if "acne" in profile.concerns:
            morning_routine.append({
                "step": 2,
                "product_type": "Treatment",
                "recommendation": "BHA toner or serum",
                "ingredients": ["salicylic acid 2%", "niacinamide"],
                "frequency": "daily",
            })
        elif "aging" in profile.concerns or "wrinkles" in profile.concerns:
            morning_routine.append({
                "step": 2,
                "product_type": "Serum",
                "recommendation": "Vitamin C serum",
                "ingredients": ["L-ascorbic acid 10-20%", "vitamin E", "ferulic acid"],
                "frequency": "daily",
            })
        elif "pigmentation" in profile.concerns:
            morning_routine.append({
                "step": 2,
                "product_type": "Serum",
                "recommendation": "Brightening serum",
                "ingredients": ["niacinamide 10%", "alpha arbutin", "kojic acid"],
                "frequency": "daily",
            })

        if profile.skin_type == "oily":
            morning_routine.append({
                "step": 3,
                "product_type": "Moisturizer",
                "recommendation": "Lightweight gel moisturizer",
                "ingredients": ["hyaluronic acid", "niacinamide"],
                "texture": "gel or gel-cream",
            })
        else:
            morning_routine.append({
                "step": 3,
                "product_type": "Moisturizer",
                "recommendation": "Hydrating cream",
                "ingredients": ["ceramides", "peptides", "hyaluronic acid"],
                "texture": "cream",
            })

        morning_routine.append({
            "step": 4,
            "product_type": "Sunscreen",
            "recommendation": "Broad spectrum SPF 30+",
            "ingredients": ["zinc oxide or chemical filters"],
            "notes": "Essential for all skin types",
        })

        evening_routine: List[Dict[str, Any]] = []
        if profile.age_range in ["30-40", "40-50", "50+"]:
            evening_routine.append({
                "step": 2,
                "product_type": "Retinol",
                "recommendation": "Start with 0.3% retinol",
                "frequency": "2-3 times per week initially",
                "notes": "Build tolerance gradually",
            })

        recommendations["morning_routine"] = morning_routine
        recommendations["evening_routine"] = evening_routine
        recommendations["weekly_treatments"] = self._get_weekly_treatments(profile)
        return recommendations

    def _format_recommendations(self, recommendations: Dict, profile: SkinProfile) -> str:
        response = f"## 🎯 Your Personalized Skincare Analysis\n\n"
        response += f"**Skin Type:** {profile.skin_type.capitalize()}\n"
        response += f"**Main Concerns:** {', '.join(profile.concerns)}\n\n"
        response += "### ☀️ Morning Routine:\n"
        for step in recommendations["morning_routine"]:
            response += f"**Step {step['step']}. {step['product_type']}**\n"
            response += f"   → {step['recommendation']}\n"
            if 'ingredients' in step:
                response += f"   *Key ingredients:* {', '.join(step['ingredients'])}\n"
            response += "\n"
        if recommendations.get("evening_routine"):
            response += "### 🌙 Evening Routine:\n"
            for step in recommendations["evening_routine"]:
                response += f"**{step['product_type']}:** {step['recommendation']}\n"
                if 'frequency' in step:
                    response += f"   *Frequency:* {step['frequency']}\n"
                response += "\n"
        if recommendations.get("weekly_treatments"):
            response += "### 📅 Weekly Treatments:\n"
            for treatment in recommendations["weekly_treatments"]:
                response += f"• **{treatment['treatment']}** - {treatment['frequency']}\n"
                response += f"  {treatment['benefits']}\n"
        response += "\n💡 **Pro Tips:**\n"
        response += "• Always patch test new products\n"
        response += "• Introduce actives gradually\n"
        response += "• Consistency is key for results\n"
        response += "• Don't forget your neck!\n"
        return response

    def _update_state(self, session: ChatSession):
        state_transitions = {
            ConversationState.GREETING: ConversationState.SKIN_TYPE,
            ConversationState.SKIN_TYPE: ConversationState.CONCERNS,
            ConversationState.CONCERNS: ConversationState.AGE_RANGE,
            ConversationState.AGE_RANGE: ConversationState.ROUTINE,
            ConversationState.ROUTINE: ConversationState.LIFESTYLE,
            ConversationState.LIFESTYLE: ConversationState.BUDGET,
            ConversationState.BUDGET: ConversationState.ALLERGIES,
            ConversationState.ALLERGIES: ConversationState.ANALYSIS,
            ConversationState.ANALYSIS: ConversationState.FOLLOWUP,
        }
        if session.state == ConversationState.SKIN_TYPE and session.profile.skin_type:
            session.state = state_transitions[session.state]
        elif session.state == ConversationState.CONCERNS and session.profile.concerns:
            session.state = state_transitions[session.state]
        elif session.state == ConversationState.AGE_RANGE and session.profile.age_range:
            session.state = state_transitions[session.state]
        elif session.state in [
            ConversationState.ROUTINE,
            ConversationState.LIFESTYLE,
            ConversationState.BUDGET,
            ConversationState.ALLERGIES,
        ]:
            session.state = state_transitions[session.state]

    def _is_profile_complete(self, profile: SkinProfile) -> bool:
        return bool(profile.skin_type and profile.concerns)

    def _generate_response(self, session: ChatSession, message: str, entities: Dict) -> tuple:
        current_flow = self.question_flow.get(session.state)
        suggestions: List[str] = []
        products: List[Dict] = []

        if session.state == ConversationState.GREETING:
            name_match = re.search(r"(?:I'm|I am|my name is|call me)\s+(\w+)", message, re.I)
            if name_match:
                session.context["name"] = name_match.group(1).capitalize()
                response = (
                    f"Nice to meet you, {session.context['name']}! "
                    + current_flow["questions"][0].split("What's your name?")[0]
                )
            else:
                response = current_flow["questions"][0]
            suggestions = ["Oily", "Dry", "Combination", "Normal", "Sensitive"]
        elif session.state == ConversationState.SKIN_TYPE:
            if entities.get("skin_type"):
                response = (
                    f"Got it! {session.profile.skin_type.capitalize()} skin needs special care. "
                    + self.question_flow[ConversationState.CONCERNS]["questions"][0]
                )
                suggestions = ["Acne", "Fine lines", "Dark spots", "Large pores", "Redness"]
            else:
                response = "Please select your skin type from the options above."
                suggestions = ["Oily", "Dry", "Combination", "Normal", "Not sure"]
        elif session.state == ConversationState.CONCERNS:
            if entities.get("concerns"):
                concern_str = ", ".join(session.profile.concerns)
                response = (
                    f"I understand you're dealing with {concern_str}. We'll address these! "
                    + self.question_flow[ConversationState.AGE_RANGE]["questions"][0]
                )
                suggestions = ["Under 20", "20-30", "30-40", "40-50", "50+"]
            else:
                response = "What skin concerns would you like to address?"
                suggestions = ["Acne", "Wrinkles", "Dark spots", "Large pores", "None"]
        elif session.state == ConversationState.ANALYSIS:
            recommendations = self.generate_recommendations(session.profile)
            session.recommendations = recommendations
            response = self._format_recommendations(recommendations, session.profile)
            from services.product_service import recommend_products
            products = recommend_products(session.profile.concerns)[:5]
            suggestions = ["Show morning routine", "Show evening routine", "Explain ingredients", "Start over"]
        else:
            if current_flow:
                response = current_flow["questions"][0]
            else:
                response = "Let me analyze your profile and create your personalized routine..."

        return response, suggestions, products

    def process_message(self, message: str, session_id: Optional[str] = None) -> ChatResponse:
        session = self.get_or_create_session(session_id)
        session.messages.append(ChatMessage(role="user", content=message))
        entities = self.extract_entities(message)
        self.update_profile(session, entities)
        response_text, suggestions, products = self._generate_response(session, message, entities)
        session.messages.append(ChatMessage(role="assistant", content=response_text))
        profile_complete = self._is_profile_complete(session.profile)
        self._update_state(session)
        self.sessions[session.session_id] = session
        return ChatResponse(
            response=response_text,
            session_id=session.session_id,
            state=session.state.value,
            suggestions=suggestions,
            products=products,
            profile_complete=profile_complete,
            requires_image=(session.state == ConversationState.ANALYSIS and "photo" in message.lower()),
        )


# ============= API Endpoints =============

chatbot = SkincareChatbot()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Advanced chatbot endpoint with conversation memory"""
    try:
        text = request.message or request.question or ""
        if not text:
            raise HTTPException(status_code=400, detail="message is required")
        return chatbot.process_message(message=text, session_id=request.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/session/{session_id}")
async def get_session(session_id: str):
    if session_id not in chatbot.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = chatbot.sessions[session_id]
    return {
        "session_id": session_id,
        "state": session.state.value,
        "profile": session.profile.dict(),
        "messages": [msg.dict() for msg in session.messages[-10:]],
        "recommendations": session.recommendations,
    }


@router.post("/chat/reset/{session_id}")
async def reset_session(session_id: str):
    if session_id in chatbot.sessions:
        del chatbot.sessions[session_id]
    return {"message": "Session reset successfully"}


@router.post("/chat/analyze-image")
async def analyze_with_image(session_id: str, file: UploadFile = File(...)):
    if session_id not in chatbot.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    from backend.ml_models.optimized_analyzer import get_optimized_analyzer
    from backend.services import image_service
    image_path = await image_service.save_upload_file(file)
    analyzer = get_optimized_analyzer()
    results = analyzer.analyze(image_path)
    session = chatbot.sessions[session_id]
    session.profile.skin_type = results.get("skin_type")
    if results.get("concerns"):
        session.profile.concerns = results["concerns"]
    response_text = (
        "\n📸 **Image Analysis Complete!**\n\n"
        f"• **Skin Type:** {results.get('skin_type','').capitalize()}\n"
        f"• **Detected Concerns:** {', '.join(results.get('concerns', []))}\n\n"
        f"{results.get('recommendations','')}\n\n"
        "Let me create a complete routine based on this analysis..."
    )
    session.state = ConversationState.ANALYSIS
    return {"response": response_text, "analysis": results, "session_id": session_id}


@router.get("/chat/export/{session_id}")
async def export_routine(session_id: str):
    if session_id not in chatbot.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = chatbot.sessions[session_id]
    return {
        "profile": session.profile.dict(),
        "recommendations": session.recommendations,
        "products": [],
        "notes": "Remember to patch test and introduce products gradually!",
    }

# End of chatbot implementation


