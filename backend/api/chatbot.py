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

    def _update_state(self, session: ChatSession, message: str):
        """Update conversation state based on current state and user input"""
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
        
        # More intelligent state transitions
        if session.state == ConversationState.GREETING:
            # Move to skin type if we got a name or any greeting response
            if any(word in message.lower() for word in ["hi", "hello", "name", "i'm", "i am", "call me"]) or len(message.strip()) > 0:
                session.state = state_transitions[session.state]
                
        elif session.state == ConversationState.SKIN_TYPE:
            # Move forward if we detected a skin type or got any reasonable response
            if session.profile.skin_type or any(skin_type in message.lower() for skin_type in ["oily", "dry", "combination", "normal", "sensitive"]):
                session.state = state_transitions[session.state]
                
        elif session.state == ConversationState.CONCERNS:
            # Move forward if we got concerns or user indicates they're done
            if session.profile.concerns or any(word in message.lower() for word in ["none", "nothing", "no concerns", "good", "fine"]):
                session.state = state_transitions[session.state]
                
        elif session.state == ConversationState.AGE_RANGE:
            # Move forward if we got age info or any number/age-related word
            age_indicators = ["teen", "twenty", "thirty", "forty", "fifty", "under", "over", "old", "age"]
            if session.profile.age_range or any(word in message.lower() for word in age_indicators) or any(char.isdigit() for char in message):
                session.state = state_transitions[session.state]
                
        elif session.state in [ConversationState.ROUTINE, ConversationState.LIFESTYLE, ConversationState.BUDGET]:
            # Move forward after any reasonable response
            if len(message.strip()) > 2:  # Any meaningful response
                session.state = state_transitions[session.state]
                
        elif session.state == ConversationState.ALLERGIES:
            # Move to analysis after allergy info (or lack thereof)
            if len(message.strip()) > 0:
                session.state = state_transitions[session.state]

    def _is_profile_complete(self, profile: SkinProfile) -> bool:
        return bool(profile.skin_type and profile.concerns)

    def _generate_response(self, session: ChatSession, message: str, entities: Dict) -> tuple:
        current_flow = self.question_flow.get(session.state)
        suggestions: List[str] = []
        products: List[Dict] = []

        if session.state == ConversationState.GREETING:
            # Handle various greeting patterns
            greeting_patterns = [
                r"(?:hi|hello|hey|good morning|good afternoon|good evening)",
                r"(?:I'm|I am|my name is|call me)\s+(\w+)",
                r"(?:help|advice|consultation|skincare)",
            ]
            
            name_match = re.search(r"(?:I'm|I am|my name is|call me)\s+(\w+)", message, re.I)
            if name_match:
                session.context["name"] = name_match.group(1).capitalize()
                response = (
                    f"Nice to meet you, {session.context['name']}! 😊 I'm your personal skincare consultant. "
                    f"I'll help you build the perfect routine tailored just for you.\n\n"
                    f"Let's start with the basics - how would you describe your skin type?"
                )
            elif any(re.search(pattern, message, re.I) for pattern in greeting_patterns):
                response = (
                    "Hello! 👋 Welcome to your personalized skincare consultation! "
                    "I'm here to help you achieve your best skin ever.\n\n"
                    "To get started, could you tell me your name? And then we'll dive into "
                    "understanding your unique skin needs!"
                )
            else:
                # Handle any other input as a general greeting
                response = (
                    "Hi there! I'm your AI skincare consultant. 🌟\n\n"
                    "I'll help you:\n"
                    "• Identify your skin type\n"
                    "• Address your specific concerns\n" 
                    "• Build a personalized routine\n"
                    "• Recommend the best products\n\n"
                    "What's your name so we can get started?"
                )
            suggestions = ["My name is...", "I need skincare help", "Oily skin", "Dry skin", "Sensitive skin"]
        elif session.state == ConversationState.SKIN_TYPE:
            if entities.get("skin_type"):
                skin_type = session.profile.skin_type.capitalize()
                skin_tips = {
                    "Oily": "Oily skin produces excess sebum, which can lead to shine and breakouts. The good news? It tends to age slower! 🌟",
                    "Dry": "Dry skin needs extra hydration and gentle care. It can feel tight but responds beautifully to the right moisture! 💧",
                    "Combination": "Combination skin is like having two skin types - oily T-zone and dry cheeks. It needs a balanced approach! ⚖️",
                    "Normal": "Lucky you! Normal skin is well-balanced, but still needs proper care to maintain its health! ✨",
                    "Sensitive": "Sensitive skin requires extra gentle care and avoiding harsh ingredients. We'll find products that love your skin back! 💕"
                }
                response = (
                    f"Perfect! {skin_type} skin it is. {skin_tips.get(skin_type, '')}\n\n"
                    f"Now, let's talk about your main skin concerns. What bothers you most about your skin? "
                    f"You can mention multiple concerns - I'm here to address them all! 🎯"
                )
                suggestions = ["Acne & breakouts", "Fine lines", "Dark spots", "Large pores", "Redness", "Dullness"]
            else:
                response = (
                    "I'd love to help you identify your skin type! Here's a quick guide:\n\n"
                    "🔸 **Oily**: Shiny, especially T-zone, prone to breakouts\n"
                    "🔸 **Dry**: Feels tight, flaky, sometimes rough texture\n" 
                    "🔸 **Combination**: Oily T-zone (forehead, nose, chin) + dry cheeks\n"
                    "🔸 **Normal**: Balanced, not too oily or dry\n"
                    "🔸 **Sensitive**: Easily irritated, reacts to products\n\n"
                    "Which one sounds most like your skin?"
                )
                suggestions = ["Oily", "Dry", "Combination", "Normal", "Sensitive", "Not sure"]
        elif session.state == ConversationState.CONCERNS:
            if entities.get("concerns"):
                concerns = session.profile.concerns
                concern_str = ", ".join(concerns)
                
                # Provide specific advice for concerns
                concern_advice = {
                    "acne": "Acne can be frustrating, but with the right ingredients like salicylic acid and niacinamide, we can get it under control! 💪",
                    "aging": "Prevention is key for aging! We'll focus on antioxidants, retinoids, and SPF to keep your skin youthful. ⏰",
                    "pigmentation": "Dark spots take patience, but ingredients like vitamin C, niacinamide, and gentle exfoliation work wonders! ✨",
                    "pores": "While we can't shrink pores permanently, we can minimize their appearance with the right routine! 🎯",
                    "redness": "Redness often indicates sensitivity or inflammation. We'll focus on gentle, soothing ingredients. 🌿",
                    "dullness": "Dull skin just needs the right exfoliation and hydration to reveal your natural glow! 🌟"
                }
                
                advice_parts = []
                for concern in concerns:
                    if concern.lower() in concern_advice:
                        advice_parts.append(concern_advice[concern.lower()])
                
                response = (
                    f"Got it! You're dealing with {concern_str}. Here's the good news:\n\n"
                    + "\n".join(f"• {advice}" for advice in advice_parts[:2]) + "\n\n"
                    + "Now, to create the perfect routine for you, which age group do you belong to? "
                    + "This helps me recommend age-appropriate products and ingredients. 🎂"
                )
                suggestions = ["Under 20", "20-30", "30-40", "40-50", "50+"]
            else:
                response = (
                    "What skin concerns would you like to address? Don't worry - everyone has them! "
                    "The more specific you are, the better I can help you. You can mention multiple concerns:\n\n"
                    "🔸 **Acne & breakouts** - pimples, blackheads, whiteheads\n"
                    "🔸 **Aging signs** - fine lines, wrinkles, loss of firmness\n"
                    "🔸 **Dark spots** - hyperpigmentation, sun spots, acne marks\n"
                    "🔸 **Large pores** - visible or enlarged pores\n"
                    "🔸 **Redness** - irritation, rosacea, sensitivity\n"
                    "🔸 **Dullness** - lack of glow, uneven texture\n\n"
                    "What's bothering you most about your skin?"
                )
                suggestions = ["Acne", "Fine lines", "Dark spots", "Large pores", "Redness", "Dullness", "Multiple concerns"]
        elif session.state == ConversationState.ANALYSIS:
            recommendations = self.generate_recommendations(session.profile)
            session.recommendations = recommendations
            response = self._format_recommendations(recommendations, session.profile)
            from services.product_service import recommend_products
            products = recommend_products(session.profile.concerns)[:5]
            suggestions = ["Show morning routine", "Show evening routine", "Explain ingredients", "Start over"]
        else:
            # Handle other states with more intelligence
            if session.state == ConversationState.AGE_RANGE:
                age_patterns = [
                    (r"\b(\d{1,2})\s*years?\s*old\b", "specific_age"),
                    (r"\bunder\s*(\d{2})\b", "under_age"),
                    (r"\b(\d{2})-(\d{2})\b", "age_range"),
                    (r"\b(\d{2})s\b", "decade"),
                ]
                
                age_found = False
                for pattern, _ in age_patterns:
                    if re.search(pattern, message.lower()):
                        age_found = True
                        break
                
                if age_found or any(age in message.lower() for age in ["teen", "twenty", "thirty", "forty", "fifty"]):
                    response = (
                        "Perfect! Age is important for skincare because our skin's needs change over time. 📅\n\n"
                        "Now, tell me about your current skincare routine. What products do you use daily? "
                        "Even if it's just water and soap, I want to know! This helps me understand what's working "
                        "and what we might need to change. 🧴"
                    )
                    suggestions = ["Just cleanser", "Cleanser + moisturizer", "Full routine", "Nothing really", "Minimal routine"]
                else:
                    response = (
                        "I'd love to know your age range to give you the best recommendations! "
                        "Different ages have different skincare priorities:\n\n"
                        "🔸 **Under 20**: Focus on gentle cleansing and sun protection\n"
                        "🔸 **20-30**: Prevention and addressing specific concerns\n"
                        "🔸 **30-40**: Anti-aging prevention and maintenance\n"
                        "🔸 **40-50**: Active anti-aging and skin barrier support\n"
                        "🔸 **50+**: Intensive care and addressing mature skin needs\n\n"
                        "Which range fits you best?"
                    )
                    suggestions = ["Under 20", "20-30", "30-40", "40-50", "50+"]
                    
            elif session.state in [ConversationState.ROUTINE, ConversationState.LIFESTYLE, ConversationState.BUDGET, ConversationState.ALLERGIES]:
                # Handle these states with more engaging responses
                state_responses = {
                    ConversationState.ROUTINE: (
                        "Great! Understanding your current routine helps me see what's working. 👍\n\n"
                        "Now let's talk lifestyle - this affects your skin more than you might think! "
                        "How many hours of sleep do you usually get? Do you wear makeup daily? "
                        "How much water do you drink? Any outdoor activities? 🌞"
                    ),
                    ConversationState.LIFESTYLE: (
                        "Lifestyle factors are so important for skin health! 🌟\n\n"
                        "Let's talk budget - I want to make sure my recommendations fit your lifestyle. "
                        "What's your monthly skincare budget? Don't worry, great skin doesn't have to be expensive! 💰"
                    ),
                    ConversationState.BUDGET: (
                        "Perfect! I'll keep that budget in mind for all my recommendations. 💝\n\n"
                        "Last question: Do you have any allergies or ingredients you want to avoid? "
                        "This could be fragrances, essential oils, specific actives like retinol, or anything "
                        "that has irritated your skin before. Better safe than sorry! 🛡️"
                    ),
                    ConversationState.ALLERGIES: (
                        "Excellent! I have all the information I need to create your perfect routine. "
                        "Let me analyze everything and create a personalized plan just for you! ✨"
                    )
                }
                response = state_responses.get(session.state, "Let me process that information...")
                suggestions = ["Continue", "Tell me more", "I'm ready for my routine"]
                
            elif current_flow:
                response = current_flow["questions"][0]
            else:
                response = "Let me analyze your profile and create your personalized routine..."

        # Add intelligent fallback for unrecognized input
        if not response or len(response) < 10:
            response = self._handle_general_input(session, message)

        return response, suggestions, products

    def _handle_general_input(self, session: ChatSession, message: str) -> str:
        """Handle general input that doesn't fit current conversation state"""
        message_lower = message.lower()
        
        # Handle common questions/requests
        if any(word in message_lower for word in ["help", "what", "how", "why", "explain"]):
            return (
                "I'm here to help you build the perfect skincare routine! 🌟\n\n"
                "I'll guide you through a few questions to understand:\n"
                "• Your skin type and concerns\n"
                "• Your age and lifestyle\n"
                "• Your budget and preferences\n\n"
                "Then I'll create a personalized routine just for you! Ready to continue?"
            )
        
        elif any(word in message_lower for word in ["product", "recommend", "suggest", "buy"]):
            if session.profile.skin_type and session.profile.concerns:
                return (
                    "I'd love to recommend products! Let me finish gathering your information "
                    "so I can give you the most personalized recommendations. We're almost done! 🎯"
                )
            else:
                return (
                    "I'll recommend the perfect products for you once I understand your skin better! "
                    "Let's continue with a few more questions first. 💫"
                )
        
        elif any(word in message_lower for word in ["routine", "steps", "order"]):
            return (
                "I'll create a complete morning and evening routine for you! "
                "Just let me gather a bit more information about your skin first. 📋"
            )
        
        elif any(word in message_lower for word in ["ingredient", "chemical", "acid", "retinol", "vitamin"]):
            return (
                "Great question about ingredients! I'll explain everything when I create your routine. "
                "Different ingredients work better for different skin types and concerns. Let's continue! 🧪"
            )
        
        elif any(word in message_lower for word in ["skip", "next", "continue", "done"]):
            return (
                "Sure! Let's move forward. I want to make sure I have enough information "
                "to give you the best recommendations possible. 🚀"
            )
        
        elif any(word in message_lower for word in ["start over", "restart", "reset", "begin again"]):
            # Reset session
            session.state = ConversationState.GREETING
            session.profile = SkinProfile()
            session.context = {}
            return (
                "No problem! Let's start fresh. 🌟\n\n"
                "Hi! I'm your personal skincare consultant. What's your name?"
            )
        
        else:
            # Generic encouraging response
            current_state_help = {
                ConversationState.GREETING: "Let's start with your name so I can personalize our conversation!",
                ConversationState.SKIN_TYPE: "Tell me about your skin type - is it oily, dry, combination, normal, or sensitive?",
                ConversationState.CONCERNS: "What skin concerns would you like to address?",
                ConversationState.AGE_RANGE: "Which age group do you belong to?",
                ConversationState.ROUTINE: "What's your current skincare routine like?",
                ConversationState.LIFESTYLE: "Tell me about your lifestyle and daily habits!",
                ConversationState.BUDGET: "What's your monthly skincare budget?",
                ConversationState.ALLERGIES: "Do you have any allergies or ingredients to avoid?"
            }
            
            help_text = current_state_help.get(session.state, "Let's continue building your profile!")
            
            return (
                f"I understand! Let me help guide you. 😊\n\n"
                f"{help_text}\n\n"
                f"Feel free to ask me anything or just answer the question above!"
            )

    def process_message(self, message: str, session_id: Optional[str] = None) -> ChatResponse:
        session = self.get_or_create_session(session_id)
        session.messages.append(ChatMessage(role="user", content=message))
        entities = self.extract_entities(message)
        self.update_profile(session, entities)
        response_text, suggestions, products = self._generate_response(session, message, entities)
        session.messages.append(ChatMessage(role="assistant", content=response_text))
        profile_complete = self._is_profile_complete(session.profile)
        self._update_state(session, message)
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
    from ml_models.optimized_analyzer import get_optimized_analyzer
    from services import image_service
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


