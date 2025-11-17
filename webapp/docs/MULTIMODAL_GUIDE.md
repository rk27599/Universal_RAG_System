# Multimodal RAG System - Complete Guide

## 🎯 Overview

The **Multimodal RAG System** extends the text-only RAG with support for **images, audio, video, charts, and diagrams**. It enables cross-modal retrieval where you can search images using text queries, find documents related to images, transcribe audio/video, and more.

---

## ✨ Features

### 🖼️ **Vision & Images**
- **CLIP Embeddings** - Text and images in shared 768-dim embedding space
- **OCR** - Extract text from scanned documents and images (Tesseract + EasyOCR)
- **Image Captioning** - Auto-generate descriptions using BLIP-2
- **Chart Detection** - Identify and process charts, graphs, diagrams
- **Cross-Modal Search** - Search images with text, vice versa

### 🎵 **Audio**
- **Whisper Transcription** - Convert speech to text (100+ languages)
- **faster-whisper** - 10x faster transcription with same quality
- **Speaker Segments** - Time-aligned transcript segments
- **Audio from Video** - Extract and transcribe audio tracks

### 🎬 **Video**
- **Frame Extraction** - Extract keyframes or uniform sampling
- **Scene Detection** - Detect scene changes automatically
- **Thumbnail Generation** - Create video previews
- **Video Metadata** - Extract duration, resolution, codec, FPS

### 🔍 **Cross-Modal Retrieval**
- **Text → Image** - Find images matching text description
- **Image → Text** - Find documents related to image content
- **Audio → Text** - Search via transcription
- **Video → Image** - Search via extracted frames
- **Hybrid Fusion** - Combine multiple query modalities

---

## 🏗️ Architecture

### Components

```
┌─────────────────────────────────────────────────────┐
│                  Multimodal RAG System              │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌───────────────┐  ┌──────────────┐              │
│  │ Text          │  │ Images       │              │
│  │ (BGE-M3)      │  │ (CLIP)       │              │
│  │ 1024-dim      │  │ 768-dim      │              │
│  └───────┬───────┘  └──────┬───────┘              │
│          │                  │                       │
│          └─────┬────────────┘                       │
│                │                                    │
│         ┌──────▼──────┐                            │
│         │  Multimodal  │                            │
│         │  Retrieval   │                            │
│         │  Service     │                            │
│         └──────┬───────┘                            │
│                │                                    │
│    ┌───────────┼───────────┐                       │
│    │           │           │                       │
│  ┌─▼─┐      ┌─▼─┐      ┌─▼─┐                     │
│  │OCR│      │Cap│      │A/V│                     │
│  └───┘      └───┘      └───┘                     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Embedding Models

| Model | Modality | Dimensions | Use Case |
|-------|----------|-----------|----------|
| **BGE-M3** | Text | 1024 | Text search, semantic retrieval |
| **CLIP ViT-L-14** | Text + Image | 768 | Cross-modal search, image retrieval |
| **BLIP-2** | Image → Text | N/A | Image captioning |
| **Whisper** | Audio → Text | N/A | Audio transcription |

---

## 📦 Installation

### 1. System Requirements

#### Required System Packages

**Ubuntu/Debian:**
```bash
# Tesseract OCR
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# FFmpeg for audio/video processing
sudo apt-get install ffmpeg

# Additional language packs (optional)
sudo apt-get install tesseract-ocr-spa tesseract-ocr-fra
```

**macOS:**
```bash
brew install tesseract
brew install ffmpeg
```

**Windows:**
- Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
- Install FFmpeg: https://ffmpeg.org/download.html

### 2. Python Dependencies

```bash
# Install all multimodal dependencies
pip install -r webapp/backend/requirements.txt

# Or install individually:
pip install open_clip_torch pillow
pip install pytesseract easyocr
pip install openai-whisper faster-whisper
pip install opencv-python ffmpeg-python
pip install transformers torch
```

### 3. Download Models

Models are downloaded automatically on first use:

- **CLIP ViT-L-14**: ~1.7 GB (via OpenCLIP)
- **Whisper Base**: ~140 MB (recommended)
- **BLIP-2 OPT-2.7B**: ~5 GB (image captioning)
- **EasyOCR**: ~300 MB per language

### 4. Database Migration

Add multimodal tables to your database:

```bash
# Run migration
python webapp/backend/scripts/migrate_add_multimodal_support.py

# Verify migration
python webapp/backend/scripts/migrate_add_multimodal_support.py --verify

# Rollback (if needed)
python webapp/backend/scripts/migrate_add_multimodal_support.py --rollback
```

---

## 🚀 Quick Start

### Example 1: Process PDF with Images

```python
from services.multimodal.embedding_service_clip import CLIPEmbeddingService
from services.multimodal.image_captioning_service import ImageCaptioningService
from services.multimodal.ocr_service import OCRService

# Initialize services
clip = CLIPEmbeddingService()
captioner = ImageCaptioningService()
ocr = OCRService()

# Process image from PDF
image_path = "data/uploads/document_page_5_image_0.jpg"

# 1. Generate CLIP embedding
image_embedding = clip.encode_image(image_path)

# 2. Generate caption
caption = captioner.generate_caption(image_path)
print(f"Caption: {caption}")

# 3. Extract text (if present)
ocr_result = ocr.extract_text(image_path)
if ocr_result:
    print(f"OCR Text: {ocr_result.text}")
    print(f"Confidence: {ocr_result.confidence:.2%}")
```

### Example 2: Cross-Modal Search

```python
from services.multimodal.multimodal_retrieval_service import (
    MultimodalRetrievalService,
    QueryType
)

# Initialize retrieval service
retrieval = MultimodalRetrievalService(
    clip_service=clip,
    document_service=doc_service
)

# Search images with text
results = retrieval.search_multimodal(
    query="flowchart showing the process",
    query_type=QueryType.TEXT,
    top_k=5,
    modality_filter=['image']  # Only return images
)

for result in results:
    print(f"Image: {result['media_path']}")
    print(f"Caption: {result['caption']}")
    print(f"Similarity: {result['similarity']:.3f}")
```

### Example 3: Audio Transcription

```python
from services.multimodal.audio_processor import AudioProcessor

# Initialize audio processor
audio_proc = AudioProcessor(model_size="base", use_faster_whisper=True)

# Transcribe audio
transcript = audio_proc.transcribe("meeting_recording.mp3")

if transcript:
    print(f"Transcript: {transcript.text}")
    print(f"Language: {transcript.language}")
    print(f"Duration: {transcript.duration:.1f}s")

    # Print segments with timestamps
    for segment in transcript.segments[:5]:
        print(f"[{segment.start_time:.1f}s] {segment.text}")
```

### Example 4: Video Frame Extraction

```python
from services.multimodal.video_processor import VideoProcessor

# Initialize video processor
video_proc = VideoProcessor()

# Get video metadata
metadata = video_proc.get_video_metadata("presentation.mp4")
print(f"Duration: {metadata.duration:.1f}s")
print(f"Resolution: {metadata.width}x{metadata.height}")

# Extract keyframes (scene changes)
keyframes = video_proc.extract_keyframes(
    "presentation.mp4",
    output_dir="video_frames/",
    threshold=30.0
)

print(f"Extracted {len(keyframes)} keyframes")

# Generate thumbnail
thumbnail = video_proc.generate_thumbnail(
    "presentation.mp4",
    "thumbnail.jpg"
)
```

---

## 🎨 Use Cases

### 1. Technical Documentation with Diagrams

**Scenario:** Process technical manuals with circuit diagrams, flowcharts

```python
# 1. Extract images from PDF
pdf_processor.process_pdf("technical_manual.pdf")

# 2. Detect diagrams
for image in extracted_images:
    is_diagram = captioner.is_chart_or_diagram(image.path)
    if is_diagram:
        # Generate detailed description
        descriptions = captioner.generate_detailed_description(image.path)
        # Store with CLIP embedding
        clip_embedding = clip.encode_image(image.path)
```

**Query:**
```python
results = retrieval.search_multimodal(
    query="circuit diagram for power supply",
    query_type=QueryType.TEXT,
    top_k=5
)
```

### 2. Scanned Document Processing

**Scenario:** OCR scanned PDFs and make them searchable

```python
# Check if PDF page is scanned
is_scanned = ocr.is_scanned_pdf_page(page_image)

if is_scanned:
    # Extract text via OCR
    ocr_result = ocr.extract_text(page_image, language='en')

    # Index OCR text for search
    chunk = create_chunk(
        content=ocr_result.text,
        metadata={'source': 'ocr', 'confidence': ocr_result.confidence}
    )
```

### 3. Meeting Analysis

**Scenario:** Transcribe and search meeting recordings

```python
# Transcribe meeting
transcript = audio_proc.transcribe("team_meeting.mp3", language="en")

# Store segments with timestamps
for segment in transcript.segments:
    create_transcript_segment(
        text=segment.text,
        start_time=segment.start_time,
        end_time=segment.end_time,
        confidence=segment.confidence
    )

# Search meeting content
results = retrieval.search_multimodal(
    query="discuss budget allocation",
    query_type=QueryType.TEXT
)
```

### 4. Video Lecture Processing

**Scenario:** Extract slides from lecture videos

```python
# Extract keyframes (slide changes)
frames = video_proc.extract_keyframes(
    "lecture.mp4",
    output_dir="slides/",
    threshold=35.0  # Detect slide transitions
)

# Process each frame
for frame in frames:
    # Generate caption
    caption = captioner.generate_caption(frame.frame_path)

    # Extract text from slide
    ocr_result = ocr.extract_text(frame.frame_path)

    # Create searchable chunk
    chunk_text = f"{caption}\n\n{ocr_result.text if ocr_result else ''}"
```

### 5. Image-Based Question Answering

**Scenario:** Ask questions about images in documents

```python
# Upload image as query
query_image = "reference_diagram.jpg"

# Find similar images and related text
results = retrieval.search_multimodal(
    query=query_image,
    query_type=QueryType.IMAGE,
    top_k=10,
    modality_filter=['image', 'text']  # Return both
)

# Pass results to vision LLM
context = "\n".join([r['content'] for r in results])
answer = vision_llm.generate(
    prompt="What is the relationship between these components?",
    image=query_image,
    context=context
)
```

---

## 📊 Performance & Optimization

### Model Selection

| Model | Size | Speed | Quality | GPU Memory |
|-------|------|-------|---------|-----------|
| **CLIP ViT-B-32** | 350 MB | Fast | Good | 2 GB |
| **CLIP ViT-L-14** | 1.7 GB | Medium | Excellent | 4 GB |
| **Whisper Tiny** | 75 MB | Very Fast | Fair | 1 GB |
| **Whisper Base** | 140 MB | Fast | Good | 1 GB |
| **Whisper Small** | 460 MB | Medium | Very Good | 2 GB |
| **BLIP-2 OPT-2.7B** | 5 GB | Slow | Excellent | 8 GB |

### Batch Processing

Process multiple files efficiently:

```python
# Batch image embedding
image_paths = ["img1.jpg", "img2.jpg", "img3.jpg"]
embeddings = clip.encode_batch(image_paths, modality=ModalityType.IMAGE, batch_size=8)

# Batch audio transcription
audio_files = ["audio1.mp3", "audio2.mp3"]
transcripts = audio_proc.transcribe_batch(audio_files)
```

### GPU Acceleration

Enable GPU for faster processing:

```python
# Check GPU availability
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0)}")

# All services auto-detect and use GPU when available
```

### Caching Strategy

Cache embeddings to avoid recomputation:

```python
# CLIP embeddings are cached in media_metadata table
# No need to regenerate for same images
```

---

## 🔧 Configuration

### OCR Configuration

```python
# Use Tesseract (fast, English)
ocr = OCRService(use_easyocr=False, languages=['en'])

# Use EasyOCR (multilingual, slower)
ocr = OCRService(use_easyocr=True, languages=['en', 'es', 'zh'])
```

### Audio Transcription Settings

```python
# Standard Whisper
audio_proc = AudioProcessor(
    model_size="base",
    use_faster_whisper=False
)

# Faster Whisper (recommended)
audio_proc = AudioProcessor(
    model_size="base",
    use_faster_whisper=True,
    device="cuda",
    compute_type="float16"  # or "int8" for even faster
)
```

### Video Processing Parameters

```python
# Uniform frame extraction
frames = video_proc.extract_frames_uniform(
    video_path,
    output_dir,
    num_frames=20  # Extract 20 frames evenly
)

# Keyframe extraction (scene detection)
keyframes = video_proc.extract_keyframes(
    video_path,
    output_dir,
    threshold=30.0,  # Lower = more keyframes
    max_frames=50
)
```

---

## 🗄️ Database Schema

### New Tables

#### `media_metadata`
Stores metadata for images, audio, video:

```sql
- chunk_id (FK to chunks)
- modality (enum: image, audio, video, chart, diagram)
- media_path (path to file)
- clip_embedding (vector(768))  -- CLIP embedding
- image_width, image_height
- audio_duration_seconds
- video_duration_seconds, video_fps
- caption (auto-generated description)
- ocr_text (extracted text)
- detected_objects (JSON)
```

#### `transcript_segments`
Time-aligned transcript segments:

```sql
- media_id (FK to media_metadata)
- segment_order
- start_time, end_time
- text
- confidence
- speaker_id (optional)
- language
```

---

## 🔍 API Endpoints (Future)

Planned multimodal endpoints:

```
POST /api/documents/upload-image
POST /api/documents/upload-audio
POST /api/documents/upload-video
POST /api/search/multimodal
POST /api/media/caption/{media_id}
POST /api/media/transcribe/{media_id}
```

---

## 📚 Examples & Tutorials

See `examples/multimodal_examples.py` for complete working examples.

---

## 🐛 Troubleshooting

### Tesseract not found
```bash
# Linux
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows: Download installer from GitHub
```

### FFmpeg not found
```bash
# Linux
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows: Download from ffmpeg.org
```

### CUDA out of memory
- Use smaller models (e.g., Whisper "base" instead of "large")
- Enable FP16: `use_fp16=True`
- Reduce batch sizes
- Process files sequentially

### Slow processing
- Enable `faster-whisper` for audio (10x speedup)
- Use GPU acceleration
- Increase batch sizes (if GPU memory allows)
- Use smaller CLIP model (ViT-B-32 instead of ViT-L-14)

---

## 🎯 Next Steps

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Run migration**: `python migrate_add_multimodal_support.py`
3. **Test with examples**: `python examples/multimodal_examples.py`
4. **Upload multimodal documents** via web UI
5. **Try cross-modal search** with your data

---

## 📖 Additional Resources

- **CLIP Paper**: https://arxiv.org/abs/2103.00020
- **Whisper Paper**: https://arxiv.org/abs/2212.04356
- **BLIP-2 Paper**: https://arxiv.org/abs/2301.12597
- **OpenCLIP**: https://github.com/mlfoundations/open_clip
- **faster-whisper**: https://github.com/guillaumekln/faster-whisper

---

**Need Help?** Open an issue on GitHub or check the documentation in `webapp/docs/`.
