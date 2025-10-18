#!/usr/bin/env python3
"""
Quick test script for MS_2.pdf with page limit
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, 'webapp/backend')

from services.pdf_processor import PDFProcessor, PDFProcessorConfig

async def test_pdf_sample():
    pdf_path = Path('webapp/backend/data/uploads/20251016_130556_MS_2.pdf')

    print(f'📄 Testing PDF: {pdf_path.name}')
    print(f'📦 File size: {pdf_path.stat().st_size / (1024*1024):.2f} MB\n')

    # Quick check
    import fitz
    doc = fitz.open(str(pdf_path))
    total_pages = len(doc)
    print(f'📊 Total pages in PDF: {total_pages}')
    print(f'⚠️  This is a VERY large PDF!\n')

    # Process only first 50 pages for testing
    print('🚀 Processing FIRST 50 PAGES only (for testing)...\n')

    # Fast config
    config = PDFProcessorConfig(
        chunk_size=1500,
        overlap=300,
        enable_image_extraction=False,  # Skip images for speed
        enable_table_extraction=True
    )

    processor = PDFProcessor(config=config)

    # Manually process limited pages
    structured_pages = []
    for page_num in range(min(50, total_pages)):
        page = doc[page_num]
        text_dict = page.get_text("dict")
        blocks = processor._process_pymupdf_blocks(text_dict, page_num + 1)
        blocks = processor._post_process_blocks_for_tables(blocks)
        structured_pages.append({
            'page_number': page_num + 1,
            'blocks': blocks
        })

        if (page_num + 1) % 10 == 0:
            print(f'  ✓ Processed {page_num + 1} pages...')

    doc.close()

    print(f'\n📝 Creating semantic chunks...')
    chunks = processor.create_semantic_chunks(structured_pages, [])

    print(f'\n✅ SUCCESS!')
    print(f'📝 Total chunks created: {len(chunks)}')
    print(f'\n📋 First 5 chunks:')
    for i, chunk in enumerate(chunks[:5], 1):
        print(f'  {i}. {chunk.heading} ({len(chunk.text.split())} words)')
        preview = chunk.text[:100].replace('\n', ' ')
        print(f'     "{preview}..."')

    print(f'\n💡 To process the FULL PDF ({total_pages} pages):')
    print(f'   - Use the web interface with background processing')
    print(f'   - Or run this overnight (estimated 30-60 minutes)')
    print(f'   - Consider splitting the PDF into smaller sections')

if __name__ == '__main__':
    asyncio.run(test_pdf_sample())
