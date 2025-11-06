# Image Support Architecture - Universal RAG System

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          UNIVERSAL RAG SYSTEM                                │
│                        Multimodal Document Processing                        │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐   │
│  │  DocumentUpload  │────▶│   File Validator │────▶│  Upload Manager  │   │
│  │   Component      │     │  (config.ts)     │     │   (api.ts)       │   │
│  └──────────────────┘     └──────────────────┘     └──────────────────┘   │
│         │                          │                         │              │
│         │ Drag & Drop              │ Check:                 │ HTTP POST    │
│         │ Browse Files             │ - File type            │ WebSocket    │
│         │                          │ - Size (50MB)          │              │
│         │                          │ - Extension            │              │
│         │                          │                        │              │
│  Supported: JPG, PNG, GIF, BMP, TIFF, WebP, PDF, HTML, TXT, JSON          │
│                                                                              │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │ HTTPS (localhost:8000)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                    FastAPI Application (main.py)                    │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│         │                                                                    │
│         │ /api/documents/upload                                             │
│         ▼                                                                    │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                Documents API (api/documents.py)                     │    │
│  │  - Validate file type and size                                      │    │
│  │  - Create document record (status: pending)                         │    │
│  │  - Start async processing task                                      │    │
│  └───────────────────────────┬────────────────────────────────────────┘    │
│                              │                                               │
│                              ▼                                               │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │           DocumentProcessingService (services/document_service.py)  │    │
│  │  - process_uploaded_file()                                          │    │
│  │  - _process_document_async() [background task]                      │    │
│  │  - _extract_content() [routes by file type]                         │    │
│  └───────────────────────────┬────────────────────────────────────────┘    │
│                              │                                               │
│        ┌─────────────────────┼─────────────────────┐                        │
│        │                     │                     │                        │
│        ▼                     ▼                     ▼                        │
│  ┌──────────┐         ┌──────────┐         ┌──────────┐                    │
│  │   HTML   │         │   PDF    │         │  IMAGE   │                    │
│  │ Processor│         │ Processor│         │ Processor│                    │
│  └──────────┘         └──────────┘         └──────────┘                    │
│        │                     │                     │                        │
│        │                     │                     │                        │
└────────┼─────────────────────┼─────────────────────┼─────────────────────────┘
         │                     │                     │
         │                     │                     │
         ▼                     ▼                     ▼
    (existing)            (existing)        ┌─────────────────────────────────┐
                                            │   IMAGE PROCESSING PIPELINE     │
                                            │  (NEW - image_processor.py)     │
                                            └─────────────────────────────────┘
                                                         │
                         ┌───────────────────────────────┼───────────────────────────────┐
                         │                               │                               │
                         ▼                               ▼                               ▼
                  ┌──────────────┐              ┌──────────────┐              ┌──────────────┐
                  │   Pillow     │              │  OCR Engine  │              │Vision Model  │
                  │  (PIL/Image) │              │              │              │   (LLaVA)    │
                  └──────────────┘              └──────────────┘              └──────────────┘
                         │                               │                               │
                         │                               │                               │
                  1. Load Image                  2. Extract Text              3. Generate Description
                  2. Validate                    ┌──────────────┐             ┌──────────────┐
                  3. Resize                      │  EasyOCR     │             │   Ollama     │
                  4. Normalize                   │  (GPU/CPU)   │             │   Server     │
                  5. Extract Metadata            │              │             │              │
                     - Dimensions                │  Pytesseract │             │  llava:7b    │
                     - Format                    │  (fallback)  │             │  llava:13b   │
                     - EXIF                      │              │             │  llava:34b   │
                     - Color mode                └──────────────┘             └──────────────┘
                  6. Generate Thumbnail                 │                               │
                         │                              │                               │
                         └──────────────────────────────┴───────────────────────────────┘
                                                        │
                                                        ▼
                                            ┌───────────────────────┐
                                            │   Combined Text       │
                                            │ OCR + Vision + Meta   │
                                            └───────────────────────┘
                                                        │
                                                        ▼
                                            ┌───────────────────────┐
                                            │  Semantic Chunking    │
                                            │  (1000 words/chunk)   │
                                            │  200 words overlap    │
                                            └───────────────────────┘
                                                        │
                                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EMBEDDING LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │         EmbeddingService (services/embedding_service_bge.py)        │    │
│  │                                                                      │    │
│  │  ┌──────────────────────────────────────────────────────────────┐  │    │
│  │  │                    BGE-M3 Model                               │  │    │
│  │  │              BAAI/bge-m3 (FlagEmbedding)                      │  │    │
│  │  │                                                                │  │    │
│  │  │  - 1024 dimensions (high quality)                             │  │    │
│  │  │  - 8,192 token context window                                 │  │    │
│  │  │  - 100+ languages supported                                   │  │    │
│  │  │  - State-of-the-art MTEB scores                               │  │    │
│  │  └──────────────────────────────────────────────────────────────┘  │    │
│  │                              │                                      │    │
│  │                              ▼                                      │    │
│  │              generate_embeddings_batch_async()                     │    │
│  │                    (GPU/CPU optimized)                             │    │
│  │                              │                                      │    │
│  └──────────────────────────────┼───────────────────────────────────┘    │
│                                 │                                          │
└─────────────────────────────────┼───────────────────────────────────────────┘
                                  │
                                  ▼
                          [1024-dim vectors]
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATABASE LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                PostgreSQL + pgvector Extension                      │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│         │                              │                                    │
│         ▼                              ▼                                    │
│  ┌──────────────┐              ┌──────────────────┐                        │
│  │  documents   │              │     chunks       │                        │
│  │   table      │◀─────────────│     table        │                        │
│  └──────────────┘    FK         └──────────────────┘                        │
│         │                              │                                    │
│  Standard Columns:             Standard Columns:                           │
│  - id, user_id                 - id, document_id                           │
│  - title, filename             - content, content_hash                     │
│  - source_type                 - chunk_order                               │
│  - processing_status           - content_type                              │
│  - total_chunks                - section_hierarchy                         │
│                                                                              │
│  IMAGE-SPECIFIC (NEW):         VECTOR Columns:                             │
│  - image_width                 - embedding_new (vector(1024))              │
│  - image_height                  → HNSW index (cosine distance)            │
│  - image_format                - embedding_model_new                       │
│  - has_ocr_text                                                             │
│  - has_vision_description      Statistics:                                 │
│  - thumbnail_path              - character_count                           │
│                                - word_count                                 │
│                                - token_count                                │
│                                                                              │
│  Indexes:                      Indexes:                                    │
│  - idx_document_user           - idx_chunk_embedding (HNSW)                │
│  - idx_document_status         - idx_chunk_document                        │
│  - idx_document_hash           - idx_chunk_order                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          RETRIEVAL LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │            Enhanced Search Service (enhanced_search_service.py)     │    │
│  │                                                                      │    │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │    │
│  │  │ Vector Search    │  │   BM25 Search    │  │   Reranker       │ │    │
│  │  │ (BGE-M3)         │  │   (Keyword)      │  │ (Cross-encoder)  │ │    │
│  │  │                  │  │                  │  │                  │ │    │
│  │  │ pgvector HNSW    │  │ rank-bm25        │  │ BGE-reranker-v2  │ │    │
│  │  │ Cosine distance  │  │ TF-IDF weights   │  │ Precision boost  │ │    │
│  │  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘ │    │
│  │           │                     │                     │           │    │
│  │           └─────────────────────┴─────────────────────┘           │    │
│  │                              │                                     │    │
│  │                    Ensemble Retriever                              │    │
│  │                  (Hybrid Fusion: α=0.5)                            │    │
│  │                              │                                     │    │
│  └──────────────────────────────┼──────────────────────────────────┘    │
│                                 │                                          │
│                                 ▼                                          │
│                        Top-K Results (5-20)                                │
│                   [Images + PDFs + HTML + Text]                            │
│                                 │                                          │
└─────────────────────────────────┼───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          GENERATION LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                LLM Factory (services/llm_factory.py)                │    │
│  │                  get_llm_service() [config: .env]                   │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│         │                                                                    │
│         ├───────────────────────────────────────┐                           │
│         ▼                                       ▼                           │
│  ┌──────────────┐                       ┌──────────────┐                   │
│  │   Ollama     │                       │    vLLM      │                   │
│  │   Service    │                       │   Service    │                   │
│  └──────────────┘                       └──────────────┘                   │
│         │                                       │                           │
│  ┌──────┴──────┐                       ┌────────┴────────┐                 │
│  │   Text LLM  │                       │  Multi-GPU LLM  │                 │
│  │  - Mistral  │                       │  - Qwen3-4B-FP8 │                 │
│  │  - Llama2   │                       │  - Any HF model │                 │
│  │  - CodeLlama│                       │                 │                 │
│  └─────────────┘                       └─────────────────┘                 │
│         │                                       │                           │
│  ┌──────┴──────┐                                                            │
│  │Vision Model │                                                            │
│  │  - LLaVA 7B │                                                            │
│  │  - LLaVA 13B│                                                            │
│  └─────────────┘                                                            │
│         │                                                                    │
│         │ generate() / generate_with_image()                                │
│         ▼                                                                    │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                    RAG Service (rag_service.py)                     │    │
│  │                                                                      │    │
│  │  1. Query expansion (multi-query)                                   │    │
│  │  2. Hybrid retrieval (vector + BM25)                                │    │
│  │  3. Reranking (cross-encoder)                                       │    │
│  │  4. Context construction                                            │    │
│  │  5. LLM generation                                                  │    │
│  │  6. Citation formatting                                             │    │
│  │                                                                      │    │
│  └──────────────────────────────────────────────────────────────────────   │
│                                 │                                          │
└─────────────────────────────────┼───────────────────────────────────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │  Final Answer   │
                         │  with Citations │
                         └─────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          COMMUNICATION LAYER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                  WebSocket (Socket.IO + Redis)                      │    │
│  │                                                                      │    │
│  │  Real-time Progress Updates:                                        │    │
│  │  - document_progress (processing stages)                            │    │
│  │  - chat_message (streaming responses)                               │    │
│  │  - search_results (retrieval feedback)                              │    │
│  │                                                                      │    │
│  │  Events:                                                             │    │
│  │  - loading_image (10%)                                               │    │
│  │  - preprocessing (20%)                                               │    │
│  │  - ocr_extraction (40%)                                              │    │
│  │  - vision_model (60%)                                                │    │
│  │  - chunking (80%)                                                    │    │
│  │  - completed (100%)                                                  │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                 │                                          │
└─────────────────────────────────┼───────────────────────────────────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │   Frontend UI   │
                         │  Progress Bar   │
                         │  Chat Interface │
                         └─────────────────┘
```

---

## Image Processing Flow Detail

### Phase 1: Upload & Validation (Frontend → Backend)

```
User Action                    Frontend                    Backend
───────────────────────────────────────────────────────────────────
1. Drag & Drop Image
   │
   ├──▶ DocumentUpload.tsx
   │    - validateFile()
   │      ✓ Check size (≤50MB)
   │      ✓ Check extension (.jpg, .png, etc.)
   │      ✓ Check MIME type
   │
   ├──▶ config.ts
   │    - allowedFileTypes[]
   │    - security.maxFileSize
   │
   └──▶ API POST /api/documents/upload
        - FormData: file + chunk_size
        - Authorization: Bearer token
               │
               ▼
        documents.py (API Handler)
        - Get current user
        - Create DocumentProcessingService
        - Call process_uploaded_file()
               │
               ▼
        document_service.py
        - Validate file extension
        - Calculate SHA-256 hash
        - Check for duplicates
        - Save to data/uploads/
        - Create Document record (status: pending)
        - Start async background task
               │
               ▼
        _process_document_async()
        [Background Task - Non-blocking]
```

### Phase 2: Image Processing (Background)

```
Background Task: _process_document_async(document_id, file_path)
─────────────────────────────────────────────────────────────────

1. Mark document as "processing" in DB
   │
   ▼
2. _extract_content(file_path, content_type)
   │
   ├─ Detect file type: .jpg, .png, etc.
   │
   ├─ Route to ImageProcessor
   │  │
   │  ├──▶ ImageProcessor.__init__(config)
   │  │     - chunk_size: 1000 words
   │  │     - overlap: 200 words
   │  │     - enable_ocr: True
   │  │     - enable_vision_model: True
   │  │     - max_image_size: (2048, 2048)
   │  │
   │  └──▶ process_image(image_path, document_id, llm_service, progress_callback)
   │        │
   │        ├─ Progress: 10% [Loading Image]
   │        │  - PIL.Image.open(image_path)
   │        │  - Extract EXIF (camera, date, software)
   │        │  - Get dimensions, format, mode
   │        │
   │        ├─ Progress: 20% [Preprocessing]
   │        │  - Convert to RGB if needed
   │        │  - Resize if > 2048x2048
   │        │  - Generate thumbnail (300x300)
   │        │
   │        ├─ Progress: 40% [OCR Extraction]
   │        │  │
   │        │  ├──▶ EasyOCR (if available)
   │        │  │    - reader = easyocr.Reader(['en'])
   │        │  │    - results = reader.readtext(image)
   │        │  │    - Extract text with bounding boxes
   │        │  │    - GPU acceleration if available
   │        │  │
   │        │  └──▶ Pytesseract (fallback)
   │        │       - pytesseract.image_to_string(image)
   │        │       - CPU-based, system-level binary
   │        │
   │        ├─ Progress: 60% [Vision Model Description]
   │        │  │
   │        │  └──▶ LLaVA via Ollama
   │        │       - Read image as base64
   │        │       - POST to http://localhost:11434/api/generate
   │        │       - Payload: {model: "llava", images: [base64_data]}
   │        │       - Prompt: "Describe this image in detail..."
   │        │       - Response: AI-generated description
   │        │
   │        ├─ Progress: 80% [Semantic Chunking]
   │        │  - Combine OCR text + vision description
   │        │  - Split by paragraphs (double newline)
   │        │  - Create chunks (1000 words + 200 overlap)
   │        │  - Preserve context boundaries
   │        │
   │        └─ Progress: 100% [Complete]
   │           - Return structured result
   │
   └─ Convert to standard document format:
      {
        'page_title': 'diagram.png',
        'url': 'file:///path/to/diagram.png',
        'total_sections': 3,
        'sections': [
          {
            'title': 'Image: diagram.png',
            'content_text': 'chunk_1_text...',
            'metadata': {
              'content_type': 'image',
              'width': 1920,
              'height': 1080,
              'format': 'PNG',
              'ocr_char_count': 450,
              'vision_char_count': 320
            }
          },
          ...
        ]
      }
      │
      ▼
3. _create_chunks(structured_content, max_chunk_size=2000)
   - Extract sections from result
   - Build section hierarchy
   - Assign chunk order (0, 1, 2, ...)
   - Add metadata (page title, domain, content type)
   │
   ▼
4. Generate Embeddings (BGE-M3)
   - embedding_service.generate_embeddings_batch_async(chunk_texts)
   - Parallel processing on GPU/CPU
   - 1024-dim vectors for each chunk
   - Progress: 40% → 95%
   │
   ▼
5. Store in Database
   - Create Chunk records with:
     - content, content_hash
     - embedding_new (1024-dim vector)
     - embedding_model_new: "BAAI/bge-m3"
     - chunk_order, content_type
     - section_hierarchy, metadata
   - Update Document record:
     - image_width, image_height
     - image_format, has_ocr_text
     - has_vision_description, thumbnail_path
     - processing_status: "completed"
     - total_chunks: N
   │
   ▼
6. Build BM25 Index
   - BM25Retriever.build_index(chunks)
   - Keyword-based search support
   │
   ▼
7. WebSocket Progress Notification
   - Emit "document_progress" event
   - Frontend updates progress bar
   │
   ▼
8. Complete
   - Document ready for RAG queries
```

### Phase 3: Query & Retrieval

```
User Query: "What is shown in the system architecture diagram?"
──────────────────────────────────────────────────────────────────

1. Frontend Chat Component
   - User types query
   - POST /api/chat/query
   │
   ▼
2. Chat API Handler
   - Validate user authentication
   - Call RAGService.search()
   │
   ▼
3. Enhanced Search Service
   │
   ├─ Step 1: Query Expansion
   │  - Generate 3 alternative queries
   │  - "system architecture overview"
   │  - "architectural diagram components"
   │  - "system design illustration"
   │
   ├─ Step 2: Hybrid Retrieval
   │  │
   │  ├──▶ Vector Search (pgvector)
   │  │    - Embed query with BGE-M3
   │  │    - HNSW index lookup (cosine distance)
   │  │    - Top-20 semantic matches
   │  │    - Includes IMAGE chunks!
   │  │
   │  ├──▶ BM25 Search (keyword)
   │  │    - Tokenize query terms
   │  │    - TF-IDF scoring
   │  │    - Top-20 keyword matches
   │  │
   │  └──▶ Ensemble Fusion
   │       - Reciprocal Rank Fusion (α=0.5)
   │       - Merge and deduplicate
   │       - Top-20 combined results
   │
   ├─ Step 3: Reranking
   │  - Cross-encoder model (BGE-reranker-v2)
   │  - Precision boost
   │  - Top-5 final results
   │
   └─ Step 4: Context Construction
      - Fetch full chunk content from DB
      - Include metadata (source, page, content_type)
      - Sort by relevance score
      │
      ▼
4. LLM Generation (Ollama/vLLM)
   - System prompt: "Material Studio Expert"
   - Context: Top-5 chunks (including images!)
   - User query
   - Temperature: 0.7
   - Max tokens: 4096
   │
   ▼
5. Stream Response
   - WebSocket: chat_message events
   - Markdown formatting
   - Citations: [Source: diagram.png]
   │
   ▼
6. Frontend Display
   - Render markdown
   - Show sources with similarity scores
   - Highlight image sources
```

---

## Data Flow Diagram

```
┌─────────────┐
│   Image     │
│  File Upload│
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│              Image Processing Pipeline               │
├──────────────────────────────────────────────────────┤
│                                                       │
│  ┌────────┐    ┌─────────┐    ┌────────────┐       │
│  │ Pillow │───▶│   OCR   │───▶│   Vision   │       │
│  │  Load  │    │ Extract │    │   Model    │       │
│  └────────┘    └─────────┘    └────────────┘       │
│       │             │                │               │
│       │             │                │               │
│    Metadata      OCR Text      AI Description       │
│       │             │                │               │
│       └─────────────┴────────────────┘               │
│                     │                                 │
│                     ▼                                 │
│            ┌────────────────┐                        │
│            │ Combined Text  │                        │
│            │ (Multimodal)   │                        │
│            └────────┬───────┘                        │
│                     │                                 │
│                     ▼                                 │
│            ┌────────────────┐                        │
│            │ Semantic Chunks│                        │
│            │ (3-5 per image)│                        │
│            └────────┬───────┘                        │
│                     │                                 │
└─────────────────────┼─────────────────────────────────┘
                      │
                      ▼
            ┌─────────────────┐
            │  BGE-M3 Embedding│
            │  (1024-dim)      │
            └─────────┬────────┘
                      │
                      ▼
            ┌──────────────────────────┐
            │  PostgreSQL + pgvector   │
            ├──────────────────────────┤
            │  documents table:        │
            │  - image_width           │
            │  - image_height          │
            │  - has_ocr_text: true    │
            │  - has_vision: true      │
            │                          │
            │  chunks table:           │
            │  - content (combined)    │
            │  - embedding_new (vec)   │
            │  - content_type: 'image' │
            │  - metadata (OCR stats)  │
            └──────────┬───────────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │   HNSW Vector Index │
            │   (Cosine Distance) │
            └──────────┬──────────┘
                       │
                       ▼
              ┌────────────────┐
              │  BM25 Index    │
              │ (Keyword)      │
              └────────┬───────┘
                       │
            ┌──────────┴──────────┐
            │                     │
            ▼                     ▼
    ┌──────────────┐      ┌──────────────┐
    │Vector Search │      │ BM25 Search  │
    │ (Semantic)   │      │ (Keyword)    │
    └──────┬───────┘      └──────┬───────┘
           │                     │
           └──────────┬──────────┘
                      │
                      ▼
              ┌───────────────┐
              │ Ensemble      │
              │ Retrieval     │
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │ Reranker      │
              │ (Precision)   │
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │ Top-K Results │
              │ (Images + Docs)│
              └───────┬───────┘
                      │
                      ▼
              ┌────────────────┐
              │ LLM Generation │
              │ (Ollama/vLLM)  │
              └────────┬───────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Answer with     │
              │ Citations       │
              └─────────────────┘
```

---

## Component Interaction Matrix

| Component | Depends On | Produces | Used By |
|-----------|-----------|----------|---------|
| **ImageProcessor** | Pillow, EasyOCR, Pytesseract, LLM Service | Structured content (text + metadata) | DocumentService |
| **EasyOCR** | PyTorch, CUDA (optional) | Extracted text from image | ImageProcessor |
| **LLaVA (Ollama)** | Ollama server, LLaVA model | AI image descriptions | ImageProcessor |
| **DocumentService** | ImageProcessor, EmbeddingService, DB | Document + Chunks in database | Upload API |
| **EmbeddingService** | BGE-M3 model, PyTorch | 1024-dim embeddings | DocumentService, RAGService |
| **PostgreSQL** | pgvector extension | Persistent storage | DocumentService, RAGService |
| **EnhancedSearchService** | BM25Retriever, Reranker, DB | Ranked search results | RAGService |
| **RAGService** | EnhancedSearchService, LLM Service | Generated answers with context | Chat API |
| **LLM Service** | Ollama/vLLM server | Text/vision generation | RAGService, ImageProcessor |

---

## Technology Stack Summary

### Image Processing Stack
```
┌─────────────────────────────────────────┐
│ Input Layer                             │
├─────────────────────────────────────────┤
│ - Pillow 10.1.0 (image I/O)            │
│ - Python pathlib (file handling)       │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ OCR Layer                               │
├─────────────────────────────────────────┤
│ - EasyOCR 1.7.0 (GPU, 100+ langs)      │
│ - Pytesseract 0.3.10 (CPU fallback)    │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ Vision Layer                            │
├─────────────────────────────────────────┤
│ - LLaVA 7B/13B/34B (via Ollama)        │
│ - Base64 image encoding                │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ Embedding Layer                         │
├─────────────────────────────────────────┤
│ - BGE-M3 (BAAI/bge-m3)                 │
│ - FlagEmbedding 1.3.5                  │
│ - PyTorch 2.6.0+cu124                  │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ Storage Layer                           │
├─────────────────────────────────────────┤
│ - PostgreSQL 14+                        │
│ - pgvector 0.2.4 extension             │
│ - HNSW vector index                    │
└─────────────────────────────────────────┘
```

---

## Configuration Examples

### Minimal Setup (OCR Only)
```python
config = ImageProcessorConfig(
    enable_ocr=True,
    enable_vision_model=False,  # Skip LLaVA
    chunk_size=1000,
    ocr_languages=['en']
)
```

### Maximum Quality
```python
config = ImageProcessorConfig(
    enable_ocr=True,
    enable_vision_model=True,
    chunk_size=2000,
    max_image_size=(4096, 4096),  # Keep full resolution
    image_quality=95,
    ocr_languages=['en', 'es', 'fr', 'de']
)
```

### Fast Processing
```python
config = ImageProcessorConfig(
    enable_ocr=True,
    enable_vision_model=False,
    chunk_size=500,
    max_image_size=(1024, 1024),  # Smaller
    generate_thumbnail=False       # Skip thumbnails
)
```

---

## Performance Metrics

| Metric | Small Image | Medium Image | Large Image |
|--------|-------------|--------------|-------------|
| **Size** | <500KB | 500KB-2MB | 2MB-10MB |
| **Dimensions** | <1000px | 1000-2500px | >2500px |
| **OCR Time** | 5-10s | 10-20s | 20-40s |
| **Vision Time** | 10-15s | 15-25s | 25-45s |
| **Embedding Time** | 3-5s | 5-8s | 8-15s |
| **Total Time** | 20-35s | 35-60s | 60-110s |
| **Memory** | ~200MB | ~400MB | ~800MB |
| **Chunks Generated** | 1-3 | 3-5 | 5-10 |

---

## Security & Privacy

### Local-Only Architecture
```
✅ All processing happens locally
✅ No external API calls (except optional LLaVA)
✅ Data never leaves your machine
✅ GDPR/HIPAA compliant (local deployment)
```

### Data Flow Security
```
User Upload → Local Validation → Local Storage → Local Processing →
Local DB → Local Search → Local LLM → User Response

NO cloud services involved!
```

---

**Architecture Version:** 1.0.0
**Last Updated:** December 2024
**Status:** ✅ Production Ready
