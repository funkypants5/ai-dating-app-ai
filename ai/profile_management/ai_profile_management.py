import os
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

load_dotenv(".env")

def init_ai():
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    model = init_chat_model("gpt-3.5-turbo", model_provider="openai")
    return model

