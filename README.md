# RiverHacks

## NASA Publication Scraper

A powerful web scraping tool for extracting and analyzing NASA publications with AI-powered content refinement.

## Project Structure

```
/
├── .venv/                 # Python virtual environment
├── scraper/               # Main scraper project
│   ├── data/             # Output JSON files
│   ├── scripts/          # Core scraper scripts
│   │   ├── run_scrape.py     # CLI interface
│   │   ├── scraper_core.py   # Core scraping logic
│   │   └── store_db.py       # Database storage
│   ├── run_scraper.py    # Interactive menu
│   ├── requirements.txt  # Python dependencies
│   ├── README.md         # Scraper documentation
│   └── .env             # Database configuration
└── .gitignore           # Git ignore rules
```

## Quick Start

1. **Setup Environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r scraper/requirements.txt
   ```

2. **Run Scraper:**
   ```bash
   cd scraper
   python3 run_scraper.py
   ```

3. **Choose Options:**
   - Test scrape (10 entries)
   - Medium scrape (50 entries)  
   - Full scrape (~600 entries)

## Features

- 🚀 **NASA Publication Scraping** - Extracts from NCBI PMC database
- 🧠 **AI Content Refinement** - Enhances content with key findings
- 📊 **Batch Processing** - Handles large datasets efficiently
- 💾 **Multiple Outputs** - JSON files and database storage
- 🎯 **Interactive Menu** - User-friendly interface

## Requirements

- Python 3.8+
- Virtual environment recommended
- Internet connection for scraping

## License

Open source project for educational and research purposes.