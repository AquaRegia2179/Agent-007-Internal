import os

# ...existing code...
small_model = "llama8b"
large_model = "gemini"

def _get_model_name(default: str) -> str:
    return os.getenv("MODEL", default).strip().lower()

def loadSmallModel():
    
    model_name = _get_model_name(small_model)

    if model_name == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model='gemini-2.5-flash',
            temperature=0,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
    elif model_name == "mistral":
        from langchain_mistralai.chat_models import ChatMistralAI
        return ChatMistralAI(
            api_key=os.getenv("MISTRAL_API_KEY"),
            model="mistral-large-latest"
        )
    elif model_name in ("llama8b", "llama-8b"):
        from langchain_groq import ChatGroq
        return ChatGroq(
            temperature=0,
            model_name="llama-3.1-8b-instant",
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
    else:
        raise ValueError(f"Unsupported MODEL='{model_name}'. Set MODEL env var to one of: gemini, mistral, llama8b")

def loadHeavyModel():

    model_name = _get_model_name(large_model)

    if model_name == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model='gemini-2.5-pro',
            temperature=0,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
    elif model_name == "mistral":
        from langchain_mistralai.chat_models import ChatMistralAI
        return ChatMistralAI(
            api_key=os.getenv("MISTRAL_API_KEY"),
            model="mistral-large-latest"
        )
    elif model_name in ("llama8b", "llama-8b"):
        from langchain_groq import ChatGroq
        return ChatGroq(
            temperature=0,
            model_name="llama-3.1-8b-instant",
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
    else:
        raise ValueError(f"Unsupported MODEL='{model_name}'. Set MODEL env var to one of: gemini, mistral, llama8b")
