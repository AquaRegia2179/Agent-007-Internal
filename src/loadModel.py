import os
small_model = "gpt-oss-20b"
large_model = "gpt-oss-20b"

def loadSmallModel():
    if small_model == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model='gemini-2.5-pro', temperature=0, google_api_key=os.getenv("GOOGLE_API_KEY"))
    elif small_model == "mistral":
        from langchain_mistralai.chat_models import ChatMistralAI
        return ChatMistralAI(api_key=os.getenv("MISTRAL_API_KEY"), model="mistral-large-latest")
    elif small_model == "llama8b":
        from langchain_groq import ChatGroq
        return ChatGroq( temperature=0, model_name="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY"))
    elif small_model == "gpt-oss-20b":
        from langchain_groq import ChatGroq
        return ChatGroq( temperature=0, model_name="openai/gpt-oss-20b", groq_api_key=os.getenv("GROQ_API_KEY"))

def loadHeavyModel():
    if large_model == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model='gemini-2.5-pro', temperature=0, google_api_key=os.getenv("GOOGLE_API_KEY"))
    elif large_model == "mistral":
        from langchain_mistralai.chat_models import ChatMistralAI
        return ChatMistralAI(api_key=os.getenv("MISTRAL_API_KEY"), model="mistral-large-latest")
    elif large_model == "llama8b":
        from langchain_groq import ChatGroq
        return ChatGroq( temperature=0, model_name="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY"))
    elif large_model == "gpt-oss-20b":
        from langchain_groq import ChatGroq
        return ChatGroq( temperature=0, model_name="openai/gpt-oss-20b", groq_api_key=os.getenv("GROQ_API_KEY"))
