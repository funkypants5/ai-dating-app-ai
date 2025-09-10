import os
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

load_dotenv(".env")

def init_ai():
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
    model = init_chat_model("gemini-2.5-flash", model_provider="google_genai")
    return model

