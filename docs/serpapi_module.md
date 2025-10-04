# 🧠 SerpAPI Research Pipeline Module
**Author:** Sinan Demir  
**Date:** 2025-10-05  
**Project:** NASA Space Biology Knowledge Engine – RiverHacks

---

## 🧩 Overview

This module provides a **Python-based pipeline** to fetch academic research papers from **Google Scholar** using the [SerpAPI](https://serpapi.com/) service, automatically download **open-access PDFs**, extract their full text, and store the results in a structured format ready for further AI processing (e.g., embeddings or vector search).

It acts as the **data ingestion layer** for the team’s “Space Biology Knowledge Engine”.

---

## ⚙️ Folder Structure

```
bio_knowledge_engine/
│
├── config.py                  # Loads API keys from .env
├── __init__.py
└── search/
    ├── __init__.py
    └── serpapi_client.py      # Core logic for SerpAPI + PDF extraction

data/
├── pdfs/                      # Extracted open-access paper text (auto-generated)
└── json/                      # Combined metadata and summaries (auto-generated)

test.py                        # Runs the pipeline
requirements.txt               # Dependencies
.gitignore                     # Keeps repo clean
```

---

## 🚀 Setup & Usage

### 1. Clone the repository
```bash
git clone <repo-url>
cd RiverHacks
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
.env\Scriptsctivate     # on Windows
# OR
source venv/bin/activate    # on macOS/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up your SerpAPI key
Option 1: Temporary (PowerShell)
```bash
$env:SERPAPI_KEY = "your_real_serpapi_key_here"
```

Option 2: Permanent (recommended)
Create a `.env` file in your root directory:
```
SERPAPI_KEY=your_real_serpapi_key_here
```

---

## 🧩 How It Works

1. **Fetch data from SerpAPI (Google Scholar)**
   - Uses the official `serpapi` library.
   - Queries biology or space-related topics.
   - Collects titles, links, snippets, and publication info.

2. **Detect & download PDFs**
   - Identifies open-access papers (via `resources` → `file_format == PDF`).
   - Downloads the PDF with `requests`.

3. **Extract readable text**
   - Converts PDF pages into text using `PyMuPDF (fitz)`.

4. **Save and structure results**
   - Saves extracted text files under `/data/pdfs/`.
   - Creates a JSON summary file under `/data/json/`.

---

## 🧠 Example Usage

### Run the Test Script
```bash
python test.py
```

Example console output:
```
✅ SERPAPI_KEY detected. Starting test...

🧠 Result 1: Overview of the NASA Microgravity Combustion Program
🔗 https://arc.aiaa.org/doi/pdf/10.2514/2.531
📄 Extracted PDF text (134,872 chars)
✅ Saved PDF text to data/pdfs/paper_1.txt
```

Generated JSON file:
```
data/json/microgravity_results.json
```

---

## 📁 Example JSON Output

```json
{
  "title": "Overview of the NASA microgravity combustion program",
  "link": "https://arc.aiaa.org/doi/pdf/10.2514/2.531",
  "snippet": "… overview of NASA microgravity combustion …",
  "publication_info": "MK King, HD Ross - AIAA journal, 1998 - arc.aiaa.org",
  "pdf_path": "data/pdfs/paper_1.txt",
  "summary": "Combustion experiments in microgravity...",
  "pdf_preview": "AIAA JOURNAL Vol. 36, No. 8..."
}
```

---

## 🧩 Function Reference

### `fetch_scholar_results(query: str, num_results: int = 5) -> list[dict]`
Fetches academic results from Google Scholar using SerpAPI.

**Args:**
- `query`: Search term (e.g., `"microgravity biology NASA"`)
- `num_results`: Number of results to retrieve

**Returns:**
List of dictionaries with:
- `title`
- `link`
- `snippet`
- `publication_info`
- `pdf_text` (if available)

---

## ⚙️ Dependencies

All dependencies are listed in `requirements.txt`:

```
serpapi
PyMuPDF
requests
python-dotenv
```

Install with:
```bash
pip install -r requirements.txt
```

---

## 🧭 Future Extensions

- Integrate **FAISS** or **Chroma** for semantic search
- Build a **Flask/FastAPI** endpoint for team chatbot access
- Add automated query refresh scheduling
- Implement vector embeddings with OpenAI API

---

## 👥 Team Notes

- **Do not commit `/data/` or `venv/` folders.**
- Make sure `.env` and `.gitignore` are set correctly.
- For debugging, run:
  ```bash
  python -i test.py
  ```
  and explore results interactively.

---

*Maintained by Sinan Demir*
