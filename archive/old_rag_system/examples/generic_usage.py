#!/usr/bin/env python3
"""
Generic Usage Example for Any Website RAG System
Shows how to use the generic RAG system with any website
"""

import sys
import os

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag_system import RAGSystem


def demo_fastapi_docs():
    """Demo with FastAPI documentation"""

    print("🚀 Generic RAG System - FastAPI Documentation Demo")
    print("=" * 60)

    rag_system = RAGSystem()

    # Scrape FastAPI documentation
    start_urls = ["https://fastapi.tiangolo.com/"]

    print("\n📚 Scraping FastAPI documentation...")
    success = rag_system.scrape_and_process_website(
        start_urls=start_urls,
        max_pages=15,
        output_file="data/fastapi_docs.json",
        same_domain_only=True,
        max_depth=2
    )

    if not success:
        print("❌ Failed to scrape FastAPI docs. Trying to load existing data...")
        success = rag_system.process_structured_documents("data/fastapi_docs.json")

    if not success:
        print("❌ No data available. Please check internet connection.")
        return

    # Test queries
    test_queries = [
        "How to create a FastAPI application?",
        "What is dependency injection?",
        "How to handle POST requests?",
        "Path parameters and query parameters",
        "Authentication and security",
        "Database integration with SQLAlchemy"
    ]

    print(f"\n🔍 Testing {len(test_queries)} queries...")
    print("="*60)

    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: '{query}'")
        print("-" * 40)

        result = rag_system.demo_query(query, top_k=3)
        print(result)


def demo_any_website():
    """Demo with any website (configurable)"""

    print("🚀 Generic RAG System - Any Website Demo")
    print("=" * 50)

    # You can change these URLs to any website you want
    websites_to_try = [
        {
            "name": "Python.org Documentation",
            "urls": ["https://docs.python.org/3/"],
            "max_pages": 10,
            "output_file": "data/python_docs.json",
            "queries": [
                "What are Python data types?",
                "How to use functions?",
                "Object-oriented programming",
                "Exception handling",
                "File operations"
            ]
        },
        {
            "name": "Flask Documentation",
            "urls": ["https://flask.palletsprojects.com/"],
            "max_pages": 8,
            "output_file": "data/flask_docs.json",
            "queries": [
                "How to create a Flask app?",
                "Routing and URL building",
                "Templates with Jinja2",
                "Request handling",
                "Session management"
            ]
        },
        {
            "name": "Django Documentation",
            "urls": ["https://docs.djangoproject.com/"],
            "max_pages": 12,
            "output_file": "data/django_docs.json",
            "queries": [
                "Django models and databases",
                "URL patterns and views",
                "Django admin interface",
                "Forms and validation",
                "Authentication system"
            ]
        }
    ]

    # Let user choose which website to demo
    print("\nAvailable websites to demo:")
    for i, site in enumerate(websites_to_try, 1):
        print(f"{i}. {site['name']}")

    print("\n0. Use custom URLs")

    choice = input("\nEnter choice (1-3, or 0 for custom): ").strip()

    if choice == "0":
        # Custom URLs
        custom_urls = input("Enter starting URL(s) (comma-separated): ").strip().split(",")
        custom_urls = [url.strip() for url in custom_urls if url.strip()]

        if not custom_urls:
            print("❌ No URLs provided")
            return

        website_config = {
            "name": "Custom Website",
            "urls": custom_urls,
            "max_pages": 10,
            "output_file": "data/custom_website_docs.json",
            "queries": [
                "What is this website about?",
                "Main features or topics",
                "Getting started guide",
                "Documentation or tutorials",
                "Key concepts explained"
            ]
        }
    else:
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(websites_to_try):
                website_config = websites_to_try[choice_idx]
            else:
                print("❌ Invalid choice")
                return
        except ValueError:
            print("❌ Invalid choice")
            return

    print(f"\n📚 Processing {website_config['name']}...")

    rag_system = RAGSystem()

    success = rag_system.scrape_and_process_website(
        start_urls=website_config["urls"],
        max_pages=website_config["max_pages"],
        output_file=website_config["output_file"],
        same_domain_only=True,
        max_depth=2
    )

    if not success:
        print(f"❌ Failed to scrape {website_config['name']}. Trying to load existing data...")
        success = rag_system.process_structured_documents(website_config["output_file"])

    if not success:
        print("❌ No data available. Please check URLs and internet connection.")
        return

    # Test queries
    print(f"\n🔍 Testing queries for {website_config['name']}...")
    print("="*60)

    for i, query in enumerate(website_config["queries"], 1):
        print(f"\n{i}. Query: '{query}'")
        print("-" * 40)

        result = rag_system.demo_query(query, top_k=3)
        print(result)


def demo_with_existing_data():
    """Demo using existing scraped data"""

    print("🚀 Generic RAG System - Using Existing Data")
    print("=" * 50)

    # Check for existing data files
    data_dir = "data"
    existing_files = []

    if os.path.exists(data_dir):
        for filename in os.listdir(data_dir):
            if filename.endswith("_docs.json") or filename.endswith("website_docs.json"):
                existing_files.append(filename)

    if not existing_files:
        print("❌ No existing data files found in data/ directory")
        print("Run scraping first or check file names")
        return

    print("Available data files:")
    for i, filename in enumerate(existing_files, 1):
        print(f"{i}. {filename}")

    choice = input(f"\nChoose file (1-{len(existing_files)}): ").strip()

    try:
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(existing_files):
            selected_file = os.path.join(data_dir, existing_files[choice_idx])
        else:
            print("❌ Invalid choice")
            return
    except ValueError:
        print("❌ Invalid choice")
        return

    # Load and process
    rag_system = RAGSystem()
    success = rag_system.process_structured_documents(selected_file)

    if not success:
        print("❌ Failed to load data file")
        return

    print(f"✅ Loaded data from {selected_file}")

    # Interactive query mode
    print("\n🔍 Interactive Query Mode")
    print("Enter queries (type 'quit' to exit):")

    while True:
        query = input("\nQuery: ").strip()

        if query.lower() in ['quit', 'exit', 'q']:
            break

        if not query:
            continue

        print("-" * 50)
        result = rag_system.demo_query(query, top_k=3)
        print(result)


def main():
    """Main function to choose demo mode"""

    print("🌐 Generic Website RAG System")
    print("=" * 40)
    print("1. Demo with FastAPI documentation")
    print("2. Demo with any website (interactive)")
    print("3. Use existing scraped data")
    print("4. Quick test with a single URL")

    choice = input("\nChoose demo mode (1-4): ").strip()

    if choice == "1":
        demo_fastapi_docs()
    elif choice == "2":
        demo_any_website()
    elif choice == "3":
        demo_with_existing_data()
    elif choice == "4":
        quick_test()
    else:
        print("❌ Invalid choice")


def quick_test():
    """Quick test with a single URL"""

    url = input("Enter URL to scrape and test: ").strip()

    if not url:
        print("❌ No URL provided")
        return

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    print(f"🚀 Quick test with {url}")
    print("=" * 50)

    rag_system = RAGSystem()

    success = rag_system.scrape_and_process_website(
        start_urls=[url],
        max_pages=5,
        output_file="data/quick_test_docs.json",
        same_domain_only=True,
        max_depth=1
    )

    if success:
        # Test with a generic query
        query = input("\nEnter a query to test: ").strip()
        if query:
            result = rag_system.demo_query(query, top_k=3)
            print("\n" + "="*60)
            print(result)
    else:
        print("❌ Failed to scrape the website")


if __name__ == "__main__":
    main()