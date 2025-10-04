#!/usr/bin/env python3
"""Simple database storage for NASA publications"""
import json
import os
import sys
from pathlib import Path

try:
    import psycopg2
    from psycopg2.extras import Json
    from dotenv import load_dotenv
except ImportError:
    print("❌ Missing dependencies. Install with: pip install psycopg2-binary python-dotenv")
    sys.exit(1)

# Load environment from parent directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


def store_publications():
    """Store all batch files in database."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in .env file")
        return
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Create simple table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS publications (
                id SERIAL PRIMARY KEY,
                title TEXT,
                link TEXT UNIQUE,
                content JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Find batch files
        data_dir = Path(__file__).parent.parent / 'Data'
        batch_files = sorted(data_dir.glob('batch_*.json'))
        
        if not batch_files:
            print("❌ No batch files found in Data directory")
            return
        
        total_stored = 0
        for batch_file in batch_files:
            print(f"📁 Processing {batch_file.name}...")
            
            with open(batch_file, 'r') as f:
                data = json.load(f)
            
            for item in data:
                row = item.get('row', {})
                scrape = item.get('scrape', {})
                
                title = row.get('﻿Title') or row.get('Title', 'Unknown')
                link = row.get('Link', '')
                
                if link and 'error' not in scrape:
                    try:
                        cursor.execute("""
                            INSERT INTO publications (title, link, content) 
                            VALUES (%s, %s, %s)
                            ON CONFLICT (link) DO UPDATE SET 
                                content = EXCLUDED.content
                        """, (title, link, Json(scrape)))
                        total_stored += 1
                    except Exception as e:
                        print(f"⚠️  Error storing {title}: {e}")
        
        conn.commit()
        print(f"✅ Stored {total_stored} publications in database")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    store_publications()