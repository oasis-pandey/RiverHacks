#!/usr/bin/env python3
"""Simple NASA Publication Scraper Controller"""
import os
import subprocess
from pathlib import Path

def main():
    print("🚀 NASA Publication Scraper")
    print("=" * 40)
    print("1. Test scrape (10 entries)")
    print("2. Medium scrape (50 entries)")
    print("3. Full scrape (~600 entries)")
    print("0. Exit")
    print("q. Exit")
    print("=" * 40)
    
    choice = input("Choice (0-3, q): ").strip().lower()
    
    # Paths
    project_root = Path(__file__).parent
    scripts_dir = project_root / "scripts"
    data_dir = project_root / "data"
    python_exe = project_root.parent / ".venv" / "bin" / "python"
    
    data_dir.mkdir(exist_ok=True)
    
    csv_url = "https://raw.githubusercontent.com/jgalazka/SB_publications/main/SB_publication_PMC.csv"
    
    if choice == "1":
        print("\n🧪 Running test scrape...")
        subprocess.run([
            str(python_exe), str(scripts_dir / "run_scrape.py"),
            "--csv-url", csv_url, "--count", "10",
            "--output", str(data_dir / "test_10.json"), "--delay", "0.5"
        ])
        
    elif choice == "2":
        print("\n📊 Running medium scrape...")
        subprocess.run([
            str(python_exe), str(scripts_dir / "run_scrape.py"),
            "--csv-url", csv_url, "--count", "50",
            "--output", str(data_dir / "medium_50.json")
        ])
        
    elif choice == "3":
        confirm = input("This takes ~1 hour. Continue? (y/N): ")
        if confirm.lower() == 'y':
            print("\n🌍 Running full scrape...")
            subprocess.run([
                str(python_exe), str(scripts_dir / "run_scrape.py"),
                "--csv-url", csv_url,
                "--output", str(data_dir / "complete_scrape.json")
            ])
        
    elif choice in ["0", "q"]:
        print("👋 Goodbye!")
        return
        
    if choice in ["1", "2", "3"]:
        input("\nPress Enter to continue...")
        main()

if __name__ == "__main__":
    main()