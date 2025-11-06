# Image Support Guide - Universal RAG System

## Overview

The Universal RAG System now supports **multimodal image processing** with OCR text extraction and AI-powered vision model descriptions. Upload images alongside documents to extract text, generate descriptions, and query visual content through the RAG system.

**Status:** ✅ **Production Ready** (December 2024)

---

## Features

### 🖼️ Image Processing Capabilities

1. **OCR Text Extraction**
   - **EasyOCR** (preferred): GPU-accelerated, 100+ languages
   - **Pytesseract** (fallback): CPU-based, widely compatible
   - Automatic language detection
   - High accuracy for printed text and technical diagrams

2. **Vision Model Descriptions**
   - **LLaVA** integration via Ollama
   - Detailed image understanding
   - Technical content recognition
   - Code, diagrams, and chart analysis

3. **Image Preprocessing**
   - Automatic resizing for optimal OCR
   - Format conversion (RGB normalization)
   - Quality optimization
   - Thumbnail generation for preview

4. **Metadata Extraction**
   - Dimensions (width × height)
   - Image format (JPEG, PNG, etc.)
   - EXIF data (camera, date, software)
   - File size and color mode

---

## Supported Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| **JPEG** | `.jpg`, `.jpeg` | Most common, good compression |
| **PNG** | `.png` | Lossless, transparency support |
| **GIF** | `.gif` | Animations supported (first frame) |
| **BMP** | `.bmp` | Uncompressed, large files |
| **TIFF** | `.tiff` | High quality, multi-page support |
| **WebP** | `.webp` | Modern format, excellent compression |

**Max file size:** 50MB (configurable)

---

## Installation

### 1. Install Core Dependencies

```bash
# Pillow (required for all image operations)
pip install Pillow==10.1.0
```

### 2. Install OCR Engines (Choose One or Both)

#### Option A: EasyOCR (Recommended - GPU Support)
```bash
pip install easyocr==1.7.0
```

**Features:**
- ✅ GPU acceleration (CUDA support)
- ✅ 100+ languages out of the box
- ✅ High accuracy for technical diagrams
- ❌ Larger download (~1GB models)

#### Option B: Pytesseract (Fallback - CPU Only)
```bash
# Install Python wrapper
pip install pytesseract==0.3.10

# Install Tesseract binary (system-level)
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# macOS
brew install tesseract

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

**Features:**
- ✅ Lightweight, fast on CPU
- ✅ Mature, stable
- ❌ Requires system-level installation
- ❌ Lower accuracy than EasyOCR

### 3. Setup Vision Model (Optional - For AI Descriptions)

```bash
# Install LLaVA via Ollama
ollama pull llava

# Verify installation
ollama list
```

**LLaVA Features:**
- Describes image content in natural language
- Recognizes objects, scenes, and activities
- Understands technical diagrams and code
- Analyzes charts and visualizations

---

## Usage

### 1. Web Interface Upload

1. Navigate to **Documents** page
2. Click **Upload Files** or drag & drop images
3. Select one or more image files
4. Processing automatically starts:
   - **OCR extraction** (~10-30 seconds)
   - **Vision model description** (~15-45 seconds)
   - **Embedding generation** (~5-10 seconds)

**Progress Tracking:**
```
Loading Image → Preprocessing → OCR Extraction → Vision Model → Chunking → Complete
   10%             20%              40%              60%           80%       100%
```

### 2. API Upload

```python
import requests

# Upload image
files = {'file': open('diagram.png', 'rb')}
response = requests.post(
    'http://127.0.0.1:8000/api/documents/upload',
    files=files,
    headers={'Authorization': f'Bearer {token}'},
    data={'chunk_size': 1000}
)

print(response.json())
# {
#   "success": true,
#   "data": {
#     "id": 123,
#     "title": "diagram.png",
#     "status": "processing",
#     "processingMethod": "ocr_vision"
#   }
# }
```

### 3. Query Images

Once processed, images are searchable just like documents:

```python
# Search for content in images
response = requests.post(
    'http://127.0.0.1:8000/api/chat/search',
    json={
        'query': 'What does the system architecture diagram show?',
        'topK': 5,
        'documentIds': [123]  # Optional: specific image document
    }
)

# Results include OCR text + vision description
for result in response.json()['results']:
    print(f"Content: {result['content']}")
    print(f"Similarity: {result['similarity']:.2f}")
```

---

## Configuration

### Default Configuration

```python
from services.image_processor import ImageProcessorConfig

config = ImageProcessorConfig(
    # Chunking
    chunk_size=1000,                # Words per chunk
    overlap=200,                    # Overlap between chunks

    # OCR settings
    enable_ocr=True,                # Enable text extraction
    ocr_languages=['en'],           # Languages to detect

    # Vision model settings
    enable_vision_model=True,       # Enable AI descriptions

    # Image processing
    max_image_size=(2048, 2048),    # Max dimensions (width, height)
    image_quality=85,               # JPEG quality (1-100)

    # Thumbnails
    generate_thumbnail=True,        # Create preview images
    thumbnail_size=(300, 300)       # Thumbnail dimensions
)
```

### Custom Configuration Examples

#### High-Quality Processing
```python
config = ImageProcessorConfig(
    enable_ocr=True,
    enable_vision_model=True,
    max_image_size=(4096, 4096),  # Keep large images
    image_quality=95,              # Maximum quality
    ocr_languages=['en', 'es', 'fr']  # Multiple languages
)
```

#### Fast Processing (OCR Only)
```python
config = ImageProcessorConfig(
    enable_ocr=True,
    enable_vision_model=False,     # Skip AI descriptions
    max_image_size=(1024, 1024),   # Smaller images
    generate_thumbnail=False        # Skip thumbnails
)
```

#### Vision-Only (No OCR)
```python
config = ImageProcessorConfig(
    enable_ocr=False,              # Skip OCR
    enable_vision_model=True,      # Use vision model only
    chunk_size=2000                # Larger chunks for descriptions
)
```

---

## Database Schema

The `documents` table has been extended with image-specific columns:

```sql
-- Image metadata
image_width INTEGER              -- Width in pixels
image_height INTEGER             -- Height in pixels
image_format VARCHAR(20)         -- Format (JPEG, PNG, etc.)
has_ocr_text BOOLEAN            -- Whether OCR was performed
has_vision_description BOOLEAN  -- Whether vision model ran
thumbnail_path TEXT             -- Path to thumbnail
```

### Migration

```bash
# Run migration to add image support columns
cd webapp/backend
python scripts/migrate_add_image_support.py
```

---

## Architecture

### Processing Pipeline

```
Upload Image
    ↓
Validate Format & Size
    ↓
Load Image (PIL)
    ↓
Extract Metadata (EXIF, dimensions)
    ↓
Preprocess (resize, normalize)
    ↓
┌─────────────┐        ┌────────────────┐
│ OCR Engine  │        │ Vision Model   │
│ (EasyOCR)   │        │ (LLaVA)        │
└──────┬──────┘        └────────┬───────┘
       │                        │
       ├────────────────────────┤
       ↓                        ↓
   OCR Text              AI Description
       │                        │
       └────────┬───────────────┘
                ↓
       Combined Text Content
                ↓
       Semantic Chunking
                ↓
       Embedding Generation (BGE-M3)
                ↓
       Store in Database
                ↓
       Searchable via RAG
```

### Service Integration

```python
# ImageProcessor (services/image_processor.py)
#   ↓
# DocumentService (services/document_service.py)
#   ↓
# Upload API (api/documents.py)
#   ↓
# Frontend (DocumentUpload.tsx)
```

---

## Performance

### Processing Time (Average)

| Image Size | OCR Only | OCR + Vision | Total |
|------------|----------|--------------|-------|
| **Small** (<500KB) | 5-10s | 15-25s | 20-35s |
| **Medium** (500KB-2MB) | 10-20s | 25-40s | 35-60s |
| **Large** (2MB-10MB) | 20-40s | 40-70s | 60-110s |

**Factors affecting speed:**
- Image dimensions and complexity
- OCR engine (EasyOCR faster with GPU)
- Vision model size (LLaVA ~7B params)
- System hardware (GPU vs CPU)

### Memory Usage

- **Pillow:** ~100-200MB per image
- **EasyOCR:** ~1-2GB (model loading)
- **LLaVA:** ~4-8GB (Ollama managed)

---

## Best Practices

### 1. Image Quality
- ✅ Use high-resolution images for OCR (300+ DPI)
- ✅ Ensure good contrast and lighting
- ✅ Avoid heavily compressed JPEGs
- ❌ Don't use blurry or low-res images

### 2. Content Types
**Works Well:**
- Technical diagrams and flowcharts
- Screenshots with text
- Scanned documents
- Infographics and charts
- Code screenshots

**Works Poorly:**
- Handwritten text (unless very clear)
- Artistic/abstract images
- Low-contrast images
- Heavily stylized fonts

### 3. Performance Optimization
- Enable GPU for EasyOCR: `CUDA_VISIBLE_DEVICES=0`
- Process images in batches
- Use appropriate image sizes (don't upload 20MP photos)
- Disable vision model if only extracting text

---

## Troubleshooting

### OCR Not Working

**Problem:** No text extracted from image

**Solutions:**
1. Check if OCR engines are installed:
   ```bash
   python -c "import easyocr; print('EasyOCR OK')"
   python -c "import pytesseract; print('Pytesseract OK')"
   ```

2. Verify image quality:
   - Is text clearly visible?
   - Is image resolution sufficient (>300 DPI)?
   - Is contrast adequate?

3. Enable debug logging:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

### Vision Model Fails

**Problem:** LLaVA not generating descriptions

**Solutions:**
1. Check if LLaVA is installed:
   ```bash
   ollama list | grep llava
   ```

2. Pull LLaVA model:
   ```bash
   ollama pull llava
   ```

3. Verify Ollama is running:
   ```bash
   curl http://localhost:11434/api/tags
   ```

4. Check logs for connection errors:
   ```bash
   tail -f logs/app.log | grep vision
   ```

### Out of Memory

**Problem:** System runs out of RAM during processing

**Solutions:**
1. Reduce max image size:
   ```python
   config.max_image_size = (1024, 1024)
   ```

2. Disable vision model:
   ```python
   config.enable_vision_model = False
   ```

3. Process images one at a time
4. Use CPU-only mode for OCR

---

## Examples

### Example 1: Process Technical Diagram

```python
from services.image_processor import ImageProcessor, ImageProcessorConfig
from services.llm_factory import get_llm_service

# Setup
config = ImageProcessorConfig(
    enable_ocr=True,
    enable_vision_model=True,
    ocr_languages=['en']
)
processor = ImageProcessor(config)
llm_service = get_llm_service()

# Process
result = await processor.process_image(
    image_path='system_diagram.png',
    document_id=1,
    llm_service=llm_service
)

print(f"OCR Text: {result['ocr_text'][:200]}...")
print(f"Vision Description: {result['vision_description'][:200]}...")
print(f"Total Chunks: {result['metadata']['chunk_count']}")
```

### Example 2: Batch Process Screenshots

```python
import asyncio
from pathlib import Path

async def process_screenshots():
    screenshots = Path('screenshots').glob('*.png')

    for screenshot in screenshots:
        result = await processor.process_image(
            screenshot,
            document_id=None,
            llm_service=llm_service
        )

        print(f"Processed {screenshot.name}:")
        print(f"  - OCR: {len(result['ocr_text'])} chars")
        print(f"  - Chunks: {result['metadata']['chunk_count']}")

asyncio.run(process_screenshots())
```

### Example 3: OCR-Only Fast Processing

```python
# Disable vision model for speed
config = ImageProcessorConfig(
    enable_ocr=True,
    enable_vision_model=False,
    max_image_size=(1024, 1024)
)

processor = ImageProcessor(config)

result = await processor.process_image(
    image_path='document_scan.jpg',
    document_id=1
)

# Extract just the text
extracted_text = result['ocr_text']
print(f"Extracted {len(extracted_text)} characters")
```

---

## API Reference

### ImageProcessor

#### `__init__(config: ImageProcessorConfig)`
Initialize image processor with configuration.

#### `async process_image(image_path, document_id, llm_service=None, progress_callback=None) -> Dict`
Process an image with OCR and vision model.

**Returns:**
```python
{
    'page_title': str,           # Image filename
    'content_text': str,         # Combined OCR + vision
    'ocr_text': str,             # OCR only
    'vision_description': str,   # Vision model only
    'chunks': List[str],         # Semantic chunks
    'total_sections': int,       # Number of chunks
    'metadata': {
        'width': int,
        'height': int,
        'format': str,
        'ocr_char_count': int,
        'vision_char_count': int,
        'chunk_count': int,
        'processing_method': str,
        'thumbnail_path': str
    }
}
```

#### `static is_supported_format(file_path: Path) -> bool`
Check if image format is supported.

#### `static get_image_info(file_path: Path) -> Dict`
Get basic image information without processing.

---

## Limitations

1. **Handwriting Recognition:** Limited accuracy for handwritten text
2. **Artistic Images:** May not generate meaningful descriptions
3. **Multi-Page Documents:** Only first frame/page processed (use PDF for multi-page)
4. **OCR Accuracy:** Depends on image quality and text clarity
5. **Vision Model:** Requires Ollama + LLaVA installation
6. **Language Support:** OCR best for English; vision model English-only

---

## Roadmap

- [ ] Multi-page TIFF support
- [ ] Handwriting recognition (Google Vision API integration)
- [ ] Table detection in images
- [ ] Image-to-image search (CLIP embeddings)
- [ ] Batch processing API
- [ ] Advanced image preprocessing (deskew, denoise)

---

## FAQ

**Q: Can I use image search without Ollama?**
A: Yes! OCR text extraction works standalone. Vision descriptions require Ollama + LLaVA.

**Q: What's the best OCR engine?**
A: EasyOCR (GPU) for accuracy, Pytesseract (CPU) for speed. System auto-selects.

**Q: Can I process screenshots of code?**
A: Yes! OCR works well for code screenshots. Vision model also recognizes programming languages.

**Q: How much disk space do models use?**
A: EasyOCR: ~1GB, LLaVA: ~4GB. Downloaded automatically on first use.

**Q: Can I search for objects in images?**
A: Yes! Vision model descriptions are searchable (e.g., "find images with diagrams").

---

## Support

For issues, questions, or feature requests:
- GitHub Issues: `https://github.com/your-repo/issues`
- Documentation: `webapp/docs/IMAGE_SUPPORT_GUIDE.md`
- API Docs: `http://127.0.0.1:8000/docs` (when backend running)

---

**Last Updated:** December 2024
**Status:** ✅ Production Ready
**Version:** 1.0.0
