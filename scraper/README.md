# NASA Publication SmartScraper - Organized Edition

This project reads NASA publication data from GitHub CSV, scrapes each website using enhanced AI-powered content extraction, and stores results in structured JSON files and databases.

## 📁 Project Structure

```
Alchemists/
├── scraperScripts/          # All scraper and database scripts
│   ├── run_scrape.py       # Main scraping script
│   ├── store_to_database.py # Database storage script
│   └── setup_database.py   # Database setup script
├── Data/                   # All output data files
│   ├── batch_01.json      # Processed batch files
│   ├── batch_02.json      # ...
│   └── ...                # Additional scraped data
├── src/smartscraper/       # Core scraper library
│   └── scraper.py         # Scraping logic and AI refinement
├── tests/                  # Unit tests
├── .venv/                  # Python virtual environment
├── .env                    # Database configuration
├── run_scraper.py         # Master control script
└── requirements.txt       # Dependencies
```

## 🚀 Quick Start

### Easy Way (Recommended):
```bash
python run_scraper.py
```
This opens an interactive menu with all options.

### Manual Commands:

**Small test (10 entries):**
```bash
./.venv/bin/python scraperScripts/run_scrape.py --csv-url https://raw.githubusercontent.com/jgalazka/SB_publications/main/SB_publication_PMC.csv --count 10 --output Data/test_10.json --delay 0.5
```

**Full scrape (all ~600 entries):**
```bash
./.venv/bin/python scraperScripts/run_scrape.py --csv-url https://raw.githubusercontent.com/jgalazka/SB_publications/main/SB_publication_PMC.csv --output Data/complete_scrape.json --delay 1.0 --batch-size 25
```

## 🗄️ Database Storage

1. **Setup database:**
```bash
./.venv/bin/python scraperScripts/setup_database.py
```

2. **Store data:**
```bash
./.venv/bin/python scraperScripts/store_to_database.py
```

## ✨ Features

- **Organized Structure**: Clean separation of scripts, data, and source code
- **AI-Enhanced Content**: Extracts key findings, methodology, objectives
- **PMC Integration**: Special handling for PubMed Central articles
- **Batch Processing**: Saves progress incrementally
- **Database Ready**: Structured storage in Neon PostgreSQL
- **Error Resilience**: Continues processing despite individual failures
- **Rate Limiting**: Respectful to source servers

## 📊 Output

All scraped data is saved in the `Data/` directory:
- Individual batch files for progress tracking
- Combined output files for complete datasets
- Rich metadata including authors, DOIs, abstracts, full text
- AI-extracted insights and content quality metrics
