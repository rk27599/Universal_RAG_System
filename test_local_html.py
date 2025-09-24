#!/usr/bin/env python3
"""
Test script to demonstrate local HTML file processing with the modified WebScraper
"""

import os
import tempfile
from src.web_scraper import WebScraper

def create_sample_html_file():
    """Create a sample HTML file for testing"""

    sample_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Sample Documentation Page</title>
</head>
<body>
    <nav>This is navigation - should be removed</nav>

    <main>
        <h1>Main Documentation</h1>
        <p>This is the main content of the documentation page. It contains useful information that should be extracted.</p>

        <h2>Getting Started</h2>
        <p>This section explains how to get started with the library.</p>

        <pre>
# Code example
def hello_world():
    print("Hello, World!")
        </pre>

        <h2>Advanced Usage</h2>
        <p>This section covers advanced topics and best practices.</p>

        <ul>
            <li>Feature 1: Description of feature 1</li>
            <li>Feature 2: Description of feature 2</li>
            <li>Feature 3: Description of feature 3</li>
        </ul>

        <h3>Configuration Options</h3>
        <p>Here are the available configuration options:</p>

        <table>
            <tr><th>Option</th><th>Description</th><th>Default</th></tr>
            <tr><td>debug</td><td>Enable debug mode</td><td>false</td></tr>
            <tr><td>timeout</td><td>Request timeout in seconds</td><td>30</td></tr>
        </table>
    </main>

    <footer>This is footer - should be removed</footer>
</body>
</html>
"""

    # Create temporary HTML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(sample_html)
        return f.name

def test_local_html_processing():
    """Test the local HTML file processing functionality"""

    print("🧪 Testing Local HTML File Processing\n")

    # Create sample HTML file
    html_file = create_sample_html_file()
    print(f"📄 Created sample HTML file: {html_file}")

    try:
        # Initialize scraper in local mode
        scraper = WebScraper(local_mode=True)

        # Test single file processing
        print(f"\n📂 Testing single file extraction...")
        doc_structure = scraper.extract_from_local_file(html_file)

        if doc_structure:
            print(f"✅ Successfully extracted content:")
            print(f"   - Page title: {doc_structure['page_title']}")
            print(f"   - Sections: {doc_structure['total_sections']}")
            print(f"   - Domain: {doc_structure['domain']}")

            # Show section details
            for i, section in enumerate(doc_structure['sections'], 1):
                print(f"   Section {i}: {section['title']} (Level {section['level']}, {section.get('word_count', 0)} words)")

        # Test batch processing
        print(f"\n📄 Testing batch processing...")
        result = scraper.process_local_files(
            [html_file],
            output_file="data/test_local_html.json"
        )

        print(f"\n📊 Processing Results:")
        print(f"   - Documents: {len(result.get('documents', []))}")
        print(f"   - Semantic chunks: {len(result.get('semantic_chunks', []))}")

        # Show chunk examples
        chunks = result.get('semantic_chunks', [])
        if chunks:
            print(f"\n📋 Sample chunks:")
            for i, chunk in enumerate(chunks[:3], 1):
                print(f"   Chunk {i}: {chunk['title']}")
                print(f"      Type: {chunk['type']}")
                print(f"      Words: {chunk['word_count']}")
                preview = chunk['text'][:100].replace('\n', ' ')
                print(f"      Preview: {preview}...")
                print()

        return True

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

    finally:
        # Clean up temporary file
        if os.path.exists(html_file):
            os.remove(html_file)
            print(f"🧹 Cleaned up temporary file: {html_file}")

def test_find_html_files():
    """Test the HTML file discovery functionality"""

    print("\n🔍 Testing HTML File Discovery")

    scraper = WebScraper(local_mode=True)

    # Test with current directory
    html_files = scraper.find_html_files(".")
    print(f"   Found {len(html_files)} HTML files in current directory")

    for file_path in html_files[:5]:  # Show first 5
        print(f"   - {file_path}")

if __name__ == "__main__":
    print("🚀 WebScraper Local HTML Testing\n")

    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # Test local HTML processing
    success = test_local_html_processing()

    # Test file discovery
    test_find_html_files()

    if success:
        print(f"\n✅ All tests completed successfully!")
        print(f"   Check the data/test_local_html.json file for results.")
    else:
        print(f"\n❌ Some tests failed.")