from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json
import re

from typing import Optional, Dict, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_postgres import PGVector
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings


import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__))) 
from serpapi_search import fetch_scholar_results, build_structured_response

app = Flask(__name__)
CORS(app)  
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is required")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

EMBED_MODEL = os.getenv("EMBED_MODEL", "models/embedding-001")
COLLECTION = os.getenv("COLLECTION_NAME", "nasa_docs")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-pro")


embeddings = GoogleGenerativeAIEmbeddings(
    model=EMBED_MODEL,
    google_api_key=GOOGLE_API_KEY
)

try:
    vectorstore = PGVector(
        collection_name=COLLECTION,
        connection=DATABASE_URL,
        embeddings=embeddings,
        use_jsonb=True,
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    print(f"✅ Connected to Neon database with collection '{COLLECTION}'")
except Exception as e:
    retriever = None
    print(f"⚠️ Failed to connect to Neon database: {e}")
    print("RAG will be disabled. Only SerpAPI search will be available.")

model = ChatGoogleGenerativeAI(
    model=LLM_MODEL,
    google_api_key=GOOGLE_API_KEY,
    temperature=0.7,
    convert_system_message_to_human=True  
)

# ---------- Helper Functions ----------

def query_rag(user_query: str) -> Optional[Dict[str, Any]]:
    """
    Query the RAG system with user input.
    Returns response dict or None if insufficient context.
    """
    if not retriever:
        return None
    
    try:
        ctx_docs = retriever.invoke(user_query)
        context_text = "\n\n".join(d.page_content for d in ctx_docs)
        

        if not context_text.strip():
            return None
        
        system = SystemMessage(
            content=(
                "You are a NASA research assistant specializing in space biology and microgravity research.\n"
                "- Use ONLY the Retrieved Context below to answer.\n"
                "- If the context is insufficient or unrelated, say so clearly.\n"
                "- Provide accurate, scientific responses based on the research papers.\n"
                "- Be concise and informative.\n\n"
                f"### Retrieved Context ###\n{context_text}"
            )
        )
        
        # Get response from LLM
        messages = [system, HumanMessage(content=user_query)]
        response = model.invoke(messages)
        
        return {
            "source": "rag",
            "answer": response.content.strip(),
            "documents": [
                {
                    "content": doc.page_content[:200] + "...",
                    "metadata": doc.metadata
                }
                for doc in ctx_docs[:3]  
            ]
        }
    
    except Exception as e:
        print(f"❌ RAG query failed: {e}")
        return None


def query_serpapi(user_query: str, num_results: int = 3) -> Dict[str, Any]:
    """
    Fallback to SerpAPI Google Scholar search.
    """
    try:
        papers = fetch_scholar_results(user_query, num_results)
        
        if not papers:
            return {
                "source": "serpapi",
                "answer": "I couldn't find relevant research papers for your query.",
                "papers": []
            }
        
        # Build a summary response
        summary_parts = [
            f"I found {len(papers)} relevant research papers from Google Scholar:\n"
        ]
        
        for i, paper in enumerate(papers, 1):
            title = paper.get("title", "Unknown Title")
            snippet = paper.get("snippet", "")
            link = paper.get("link", "")
            
            summary_parts.append(
                f"{i}. **{title}**\n"
                f"   {snippet}\n"
                f"   [Read more]({link})\n"
            )
        
        return {
            "source": "serpapi",
            "answer": "\n".join(summary_parts),
            "papers": papers
        }
    
    except Exception as e:
        print(f"❌ SerpAPI query failed: {e}")
        return {
            "source": "serpapi",
            "answer": f"Error searching Google Scholar: {str(e)}",
            "papers": []
        }


# ---------- API Routes ----------

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "rag_enabled": retriever is not None,
        "model": LLM_MODEL,
        "database": "neon"
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint that tries RAG first, then falls back to SerpAPI.
    
    Request body:
    {
        "message": "user query",
        "force_serpapi": false  // optional, force SerpAPI search
    }
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        force_serpapi = data.get('force_serpapi', False)
        
        if not user_message:
            return jsonify({
                "error": "Message is required"
            }), 400
        
    
        if not force_serpapi and retriever:
            rag_response = query_rag(user_message)
            
            if rag_response:
                return jsonify({
                    "success": True,
                    "response": rag_response
                })
        
        # Fallback to SerpAPI
        serpapi_response = query_serpapi(user_message)
        
        return jsonify({
            "success": True,
            "response": serpapi_response
        })
    
    except Exception as e:
        print(f"❌ Chat endpoint error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/search', methods=['POST'])
def search():
    """
    Direct SerpAPI search endpoint.
    
    Request body:
    {
        "query": "search term",
        "num_results": 5  // optional, default 3
    }
    """
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        num_results = data.get('num_results', 3)
        
        if not query:
            return jsonify({
                "error": "Query is required"
            }), 400
        
        response = query_serpapi(query, num_results)
        
        return jsonify({
            "success": True,
            "response": response
        })
    
    except Exception as e:
        print(f"❌ Search endpoint error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Starting Flask server on port {port}")
    print(f"📊 RAG enabled: {retriever is not None}")
    print(f"🤖 LLM model: {LLM_MODEL}")
    print(f"🔑 Using Google Gemini API")
    print(f"🗄️ Database: Neon PostgreSQL with pgvector")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
