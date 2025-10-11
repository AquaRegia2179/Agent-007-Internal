import os
model = "gemini"

def loadModel():
    if model == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model='gemini-2.5-pro', temperature=0, google_api_key=os.getenv("GOOGLE_API_KEY"))
    elif model == "mistral":
        from langchain_mistralai.chat_models import ChatMistralAI
        return ChatMistralAI(api_key=os.getenv("MISTRAL_API_KEY"), model="mistral-large-latest")