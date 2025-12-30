from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from app.core.config import settings




def get_llm():
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=settings.OPENAI_API_KEY
    )

def get_embeddings():
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=settings.OPENAI_API_KEY
    )
