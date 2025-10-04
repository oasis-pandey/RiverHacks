import csv
import json
import os
import time
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def read_csv_from_url(csv_url: str, limit: Optional[int] = None) -> List[Dict[str, str]]:
    resp = requests.get(csv_url, timeout=20)
    resp.raise_for_status()
    text = resp.text.splitlines()
    reader = csv.DictReader(text)
    rows = []
    for i, row in enumerate(reader):
        rows.append(row)
        if limit and i + 1 >= limit:
            break
    return rows


def fallback_parse(url: str) -> Dict:
    """Enhanced HTML parser extracting comprehensive content including full text, authors, and publication info."""
    out = {"url": url}
    try:
        # Use a session with retries and a browser-like User-Agent to avoid simple 403 blocks
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=(429, 500, 502, 503, 504))
        session.mount("https://", HTTPAdapter(max_retries=retries))
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        # If this is a PMC article (contains PMC id), try the NCBI efetch XML endpoint which is more stable for content
        m = re.search(r"(PMC\d+)", url, re.IGNORECASE)
        if m:
            pmc_id = m.group(1)
            pmc_data = _fetch_pmc_via_eutils(pmc_id, session=session)
            if pmc_data:
                out.update(pmc_data)
                return out

        r = session.get(url, timeout=30, headers=headers)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Extract comprehensive content
        title = soup.title.string.strip() if soup.title and soup.title.string else None
        
        # Meta information
        meta_desc = None
        m = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        if m and m.get("content"):
            meta_desc = m.get("content").strip()

        # Extract authors
        authors = []
        author_selectors = [
            'meta[name="author"]',
            'meta[name="citation_author"]',
            '.author',
            '.authors',
            '[class*="author"]'
        ]
        for selector in author_selectors:
            elements = soup.select(selector)
            for elem in elements:
                if elem.name == 'meta':
                    content = elem.get('content', '').strip()
                    if content and content not in authors:
                        authors.append(content)
                else:
                    text = elem.get_text(strip=True)
                    if text and text not in authors:
                        authors.append(text)
            if authors:
                break

        # Extract publication date
        pub_date = None
        date_selectors = [
            'meta[name="citation_publication_date"]',
            'meta[name="citation_date"]',
            'meta[property="article:published_time"]',
            '.publication-date',
            '.pub-date'
        ]
        for selector in date_selectors:
            elem = soup.select_one(selector)
            if elem:
                if elem.name == 'meta':
                    pub_date = elem.get('content', '').strip()
                else:
                    pub_date = elem.get_text(strip=True)
                if pub_date:
                    break

        # Extract DOI
        doi = None
        doi_elem = soup.select_one('meta[name="citation_doi"]')
        if doi_elem:
            doi = doi_elem.get('content', '').strip()

        # Extract abstract
        abstract = None
        abstract_selectors = ['.abstract', '#abstract', '[class*="abstract"]', 'meta[name="description"]']
        for selector in abstract_selectors:
            elem = soup.select_one(selector)
            if elem:
                if elem.name == 'meta':
                    abstract = elem.get('content', '').strip()
                else:
                    abstract = elem.get_text(strip=True)
                if abstract and len(abstract) > 50:
                    break

        # Extract all text content
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()
        
        # Get main content
        main_content = soup.select_one('main') or soup.select_one('.content') or soup.select_one('#content') or soup
        paragraphs = [p.get_text(strip=True) for p in main_content.find_all('p') if p.get_text(strip=True)]
        full_text = '\n\n'.join(paragraphs) if paragraphs else main_content.get_text(separator='\n', strip=True)

        headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3", "h4"])][:20]
        
        out.update({
            "title": title,
            "authors": authors[:10],  # Limit to first 10 authors
            "publication_date": pub_date,
            "doi": doi,
            "abstract": abstract,
            "meta_description": meta_desc,
            "headings": headings,
            "full_text": full_text[:10000],  # Limit to first 10k chars
            "paragraphs": paragraphs[:50]  # First 50 paragraphs
        })
    except Exception as e:
        out.update({"error": str(e)})
    return out


def _fetch_pmc_via_eutils(pmc_id: str, session: Optional[requests.Session] = None) -> Optional[Dict]:
    """Fetch PMC article XML via NCBI E-utilities and extract comprehensive content.
    Returns a dict or None on failure.
    """
    session = session or requests.Session()
    # strip any leading non-uppercase form
    pmc_id = pmc_id.upper()
    efetch = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id={pmc_id}&retmode=xml"
    try:
        r = session.get(efetch, timeout=30)
        r.raise_for_status()
        # Parse XML
        soup = BeautifulSoup(r.text, "lxml-xml")
        
        # Extract title
        article_title_tag = soup.find("article-title")
        title = article_title_tag.get_text(separator=" ", strip=True) if article_title_tag else None

        # Extract authors
        authors = []
        for contrib in soup.find_all("contrib", attrs={"contrib-type": "author"}):
            name_elem = contrib.find("name")
            if name_elem:
                surname = name_elem.find("surname")
                given_names = name_elem.find("given-names")
                if surname and given_names:
                    full_name = f"{given_names.get_text(strip=True)} {surname.get_text(strip=True)}"
                    authors.append(full_name)

        # Extract publication date
        pub_date = None
        pub_date_elem = soup.find("pub-date")
        if pub_date_elem:
            year = pub_date_elem.find("year")
            month = pub_date_elem.find("month")
            day = pub_date_elem.find("day")
            if year:
                date_parts = [year.get_text(strip=True)]
                if month:
                    date_parts.insert(0, month.get_text(strip=True).zfill(2))
                if day:
                    date_parts.append(day.get_text(strip=True).zfill(2))
                pub_date = "-".join(date_parts)

        # Extract DOI
        doi = None
        doi_elem = soup.find("article-id", attrs={"pub-id-type": "doi"})
        if doi_elem:
            doi = doi_elem.get_text(strip=True)

        # Extract abstract
        abstract = None
        abstract_tag = soup.find("abstract")
        if abstract_tag:
            abstract_parts = []
            for p in abstract_tag.find_all("p"):
                text = p.get_text(strip=True)
                if text:
                    abstract_parts.append(text)
            abstract = "\n\n".join(abstract_parts) if abstract_parts else abstract_tag.get_text(strip=True)

        # Extract full body text
        body_text = []
        body = soup.find("body")
        if body:
            for p in body.find_all("p"):
                text = p.get_text(strip=True)
                if text and len(text) > 20:  # Filter out very short paragraphs
                    body_text.append(text)

        # Extract sections and headings
        sections = []
        for sec in soup.find_all("sec"):
            title_elem = sec.find("title")
            if title_elem:
                sections.append(title_elem.get_text(strip=True))

        return {
            "title": title,
            "authors": authors,
            "publication_date": pub_date,
            "doi": doi,
            "abstract": abstract,
            "full_text": "\n\n".join(body_text)[:15000],  # Limit to 15k chars
            "sections": sections,
            "paragraphs": body_text[:100]  # First 100 paragraphs
        }
    except Exception:
        return None


def try_smartscraper_parse(url: str) -> Optional[Dict]:
    """Attempt to use ScrapeGraph SmartScraper via LangChain integration.
    This function imports langchain and the integration at runtime to avoid hard dependency failures.
    If unavailable or an error occurs it returns None to let caller fallback.
    """
    try:
        # Import lazily
        from langchain.tools import tool
        # The real integration may vary; attempt to import ScrapeGraph wrapper
        from scrapegraph import SmartScraper  # type: ignore

        scraper = SmartScraper()
        result = scraper.scrape(url)
        # The scrapegraph SDK may return complex objects; try to coerce to dict
        if isinstance(result, dict):
            return {"url": url, "smartscraper": result}
        else:
            return {"url": url, "smartscraper": str(result)}
    except Exception:
        return None


def refine_content_with_ai(content: Dict) -> Dict:
    """Apply AI-powered content refinement to extract and structure key information."""
    refined = content.copy()
    
    # Clean and structure the content
    if content.get('full_text'):
        text = content['full_text']
        
        # Extract key findings/conclusions
        sentences = text.split('. ')
        key_findings = []
        conclusion_keywords = ['conclude', 'conclusion', 'results show', 'findings indicate', 
                             'demonstrates', 'suggests', 'evidence']
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in conclusion_keywords):
                if len(sentence.strip()) > 50:  # Filter out short sentences
                    key_findings.append(sentence.strip())
        
        refined['key_findings'] = key_findings[:5]  # Top 5 findings
        
        # Extract methodology mentions
        method_keywords = ['method', 'approach', 'technique', 'procedure', 'analysis', 
                          'experiment', 'study design', 'protocol']
        methodology = []
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in method_keywords):
                if len(sentence.strip()) > 30:
                    methodology.append(sentence.strip())
        
        refined['methodology'] = methodology[:3]  # Top 3 methodology mentions
        
        # Extract research objectives
        objective_keywords = ['objective', 'aim', 'purpose', 'goal', 'investigate', 
                             'examine', 'study', 'analyze']
        objectives = []
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in objective_keywords):
                if len(sentence.strip()) > 30:
                    objectives.append(sentence.strip())
        
        refined['objectives'] = objectives[:3]  # Top 3 objectives
    
    # Structure abstract into key components
    if content.get('abstract'):
        abstract = content['abstract']
        refined['structured_abstract'] = {
            'full_text': abstract,
            'word_count': len(abstract.split()),
            'has_background': any(word in abstract.lower() for word in ['background', 'introduction']),
            'has_methods': any(word in abstract.lower() for word in ['method', 'approach', 'technique']),
            'has_results': any(word in abstract.lower() for word in ['result', 'finding', 'outcome']),
            'has_conclusion': any(word in abstract.lower() for word in ['conclusion', 'conclude', 'suggest'])
        }
    
    # Clean and validate authors
    if content.get('authors'):
        cleaned_authors = []
        for author in content['authors']:
            # Remove common prefixes and clean
            clean_author = re.sub(r'^(Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)', '', author.strip())
            if len(clean_author) > 2 and not clean_author.isdigit():
                cleaned_authors.append(clean_author)
        refined['authors'] = list(dict.fromkeys(cleaned_authors))  # Remove duplicates
    
    # Add content quality metrics
    refined['content_quality'] = {
        'has_title': bool(content.get('title')),
        'has_authors': bool(content.get('authors')),
        'has_abstract': bool(content.get('abstract')),
        'has_full_text': bool(content.get('full_text')),
        'has_doi': bool(content.get('doi')),
        'text_length': len(content.get('full_text', '')),
        'abstract_length': len(content.get('abstract', ''))
    }
    
    return refined


def scrape_rows(rows: List[Dict[str, str]], url_field_names: List[str] = None, delay: float = 1.0, refine_ai: bool = True) -> List[Dict]:
    """Given rows from CSV, find a URL field and scrape each one with rate limiting and AI refinement."""
    results = []
    url_field_names = url_field_names or ["url", "link", "webpage", "website", "uri", "pmcid"]
    
    print(f"Starting to scrape {len(rows)} entries with {delay}s delay between requests...")
    
    for i, row in enumerate(rows):
        print(f"Processing {i+1}/{len(rows)}: {row.get('﻿Title', 'Unknown title')[:60]}...")
        
        # Add delay between requests to be respectful
        if i > 0:
            time.sleep(delay)
        
        # find first field that looks like a URL
        url = None
        for k, v in row.items():
            if not v:
                continue
            lowk = k.lower()
            if any(n in lowk for n in url_field_names) or v.startswith("http://") or v.startswith("https://"):
                # if value looks like a URL, use it
                if v.startswith("http://") or v.startswith("https://"):
                    url = v.strip()
                    break
                # else if key suggests URL but doesn't start with http, try to coerce
                if any(n in lowk for n in url_field_names):
                    possible = v.strip()
                    if possible.startswith("//"):
                        possible = "https:" + possible
                    elif possible.startswith("www."):
                        possible = "https://" + possible
                    if possible.startswith("http://") or possible.startswith("https://"):
                        url = possible
                        break
        
        if not url:
            results.append({"row": row, "error": "no-url-found"})
            continue

        # Try SmartScraper first, then fallback
        parsed = try_smartscraper_parse(url)
        if parsed is None:
            parsed = fallback_parse(url)
        
        # Apply AI refinement if requested
        if refine_ai and 'error' not in parsed:
            try:
                parsed = refine_content_with_ai(parsed)
            except Exception as e:
                parsed['ai_refinement_error'] = str(e)

        results.append({"row": row, "scrape": parsed})
    
    print(f"Completed scraping {len(results)} entries")
    return results


def write_json(data: List[Dict], path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
