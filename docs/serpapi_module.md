# Bio Knowledge Engine — SerpAPI Integration

## 📘 Overview
This module integrates **SerpAPI (Google Scholar)** search capabilities into the Bio Knowledge Engine. It fetches academic papers, extracts PDFs, and formats them into structured JSON for downstream AI or RAG (Retrieval-Augmented Generation) systems.

---

## 📁 Folder Structure
```
bio_knowledge_engine/
│
├── config.py                  # Stores API key or loads from .env
├── search/
│   ├── serpapi_client.py      # Handles Google Scholar API calls & PDF extraction
│   ├── __init__.py
│
├── outputs/
│   ├── pdfs/                  # Saved PDFs
│   ├── json/                  # Final structured JSON results
│
├── test.py                    # Example test runner
└── requirements.txt
```

---

## ⚙️ Installation

```bash
pip install -r requirements.txt
```

Ensure you have a **SerpAPI key** set:
- Option 1: in `.env`
- Option 2: inside `bio_knowledge_engine/config.py`
- Option 3: plain text file `api_key.txt`

Example for `.env`:
```
SERPAPI_KEY=your_serpapi_api_key_here
```

---

## 🧭 Usage Guide

### 1. Import & Use in Python

```python
from bio_knowledge_engine.search.serpapi_client import get_structured_scholar_data

query = "microgravity effects on cell biology"
data = get_structured_scholar_data(query)

# Save output to JSON
import json
with open("papers.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

### 2. Example Output
```json
[
  {
    "title": "Modeling the impact of microgravity at the cellular level",
    "link": "https://www.frontiersin.org/articles/10.3389/fcell.2020.00096/full",
    "authors": "P Bradbury, H Wu, JU Choi, AE Rowan…",
    "paragraphs": [
      "Humans are subjected to persistent gravitational force...",
      "During space flight, astronauts are exposed to microgravity...",
      "This review will discuss recent data..."
    ]
  }
]
```

### 3. Command-Line Use (Optional)
You can run the script directly:

```bash
python run_scholar.py "microgravity effects on cell biology"
```

This creates `output.json` inside your working directory.

---

## 🧠 RAG Integration Example

Your RAG teammates can easily integrate the structured JSON into a vector store using LangChain.

```python
from langchain_community.document_loaders import JSONLoader

loader = JSONLoader(file_path="papers.json", jq_schema=".[]", text_content=False)
docs = loader.load()
```

Then they can embed the documents and pass them into a retriever for Q&A.

---

## 🧩 Troubleshooting

- **403 Forbidden** → The PDF may be blocked by the host site. Only open-access files can be fetched.
- **Missing SERPAPI_KEY** → Check your `.env` or `config.py`.
- **PyMuPDF ImportError** → Ensure you install the correct library: `pip install PyMuPDF`, **not** `fitz`.

---

## 👨‍💻 Authors
**Sinan Demir** — RiverHacks Project, 2025