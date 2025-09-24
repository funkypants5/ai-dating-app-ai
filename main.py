from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ai.profile_management.ai_profile_management import init_ai
from ai.ai_lovabot.ai_lovabot import chat as lovabot_chat
from langchain_core.messages import SystemMessage, HumanMessage

# --- AI Re-ranker imports ---
from ai.discover_profiles.models import Payload
from ai.discover_profiles.ranking import rank_recommendations

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
def get_hello():
    return "Hello, World! Connected to AI"
    

@app.post("/ai/bio")
def create_bio(bio_interests: list[str]) -> list[str]:
    model = init_ai()
    prompt =""
    with open("ai/profile_management/ai_bio_generator.md", "r") as f:
        prompt = f.read()
    system_prompt = SystemMessage(content=prompt)
    interest =""
    interest = ", ".join(bio_interests)
    human_prompt = HumanMessage(content=interest)
    response = model.invoke([system_prompt, human_prompt])
    
    # Split the response into individual bios and return as list
    bios = response.content.split('\n\n')
    cleaned_bios = []
    for bio in bios:
        if bio.strip():
            if ':' in bio:
                bio = bio.split(':', 1)[1].strip()
            cleaned_bios.append(bio.strip())
    
    return cleaned_bios

@app.post("/ai/prompts")
def generate_prompt_response(request: dict) -> str:
    model = init_ai()
    
    # Read the prompt generator instructions
    with open("ai/profile_management/ai_prompt_generator.md", "r") as f:
        system_instructions = f.read()
    
    # Extract question and user's answer from request
    question = request.get("question", "")
    user_answer = request.get("answer", "")
    
    # Create the system prompt
    system_prompt = SystemMessage(content=system_instructions)
    
    # Create the human prompt with context
    human_prompt_content = f"""
Question: {question}

User's current answer: {user_answer}

Please generate an enhanced version of the user's answer that is more engaging and authentic while maintaining their original intent and personality.
"""
    
    human_prompt = HumanMessage(content=human_prompt_content)
    
    # Get AI response
    response = model.invoke([system_prompt, human_prompt])
    
    return response.content.strip()

@app.post("/ai/lovabot")
def generate_lovabot_response(request: dict):
    # Extract messages from request
    messages = request.get("messages", [])
    
    if not messages:
        return {"answer": "No messages provided."}
    
    # Use lovabot chat function with RAG
    response = lovabot_chat(messages)
    return response
    
# ==============================
# AI Re-ranker
# ==============================

@app.post("/rank/recommendations")
def rank_recommendations_endpoint(payload: Payload):
    """Rank candidate profiles based on compatibility with user."""
    return rank_recommendations(payload)
