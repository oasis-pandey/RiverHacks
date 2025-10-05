# scripts/print_embedding_dim.py
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
from dotenv import load_dotenv
load_dotenv()  # loads GOOGLE_API_KEY from .env


# pass key explicitly or rely on env var
emb = GoogleGenerativeAIEmbeddings(
    model=os.getenv("EMBED_MODEL", "gemini-embedding-001"),
    # explicit avoids ADC fallback
    google_api_key=os.environ["GOOGLE_API_KEY"],
)

dim = len(emb.embed_query("ping"))
print(dim)
