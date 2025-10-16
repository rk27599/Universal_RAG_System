# BGE-M3 Embedding Model Migration Guide

## Overview

This guide documents the migration from **all-MiniLM-L6-v2** (384-dim) to **BGE-M3** (1024-dim) for improved embedding quality and RAG performance.

## Migration Status

### ✅ Completed Steps

1. **Database Schema Updated**
   - Added `embedding_new vector(1024)` column
   - Added `embedding_model_new VARCHAR(100)` column
   - Created HNSW index: `idx_chunk_embedding_new`
   - **Files modified:** PostgreSQL database schema

2. **BGE-M3 Service Code Created**
   - **File:** `webapp/backend/services/embedding_service_bge.py`
   - Features: Dense embeddings, FP16 support, batch processing
   - GPU-optimized with progress tracking

3. **Re-embedding Script Created**
   - **File:** `reembed_with_bge_m3.py`
   - Processes all chunks in batches
   - ETA tracking and safe rollback

4. **FlagEmbedding Installation**
   - ✅ **COMPLETED:** FlagEmbedding 1.3.5 installed
   - ✅ PyTorch upgraded to 2.6.0+cu124
   - ✅ CUDA 12.4 compatibility verified

5. **Test BGE-M3 Service**
   - ✅ Model loads correctly on CUDA (RTX 3070)
   - ✅ Single embedding generation tested
   - ✅ Batch embedding generation tested
   - ✅ 1024-dimensional embeddings confirmed

6. **Run Re-embedding Process**
   - ✅ **COMPLETED:** All 10,366 chunks re-embedded
   - ✅ **Duration:** 12.4 minutes
   - ✅ **Average speed:** 13.9 chunks/second
   - ✅ **GPU Memory:** ~5GB used

7. **Update Search Queries**
   - ✅ Modified `document_service.py` to use `embedding_new`
   - ✅ Updated dimension from 384 → 1024
   - ✅ New document uploads use BGE-M3 automatically

8. **Material Studio Expert Prompt**
   - ✅ Implemented configurable system prompt
   - ✅ Default ON for RAG queries with context
   - ✅ Frontend UI with toggle and customization
   - ✅ localStorage persistence across sessions

### 📋 Future Steps

9. **Validate & Cleanup** (Optional - when ready)
   - Test query quality improvement over time
   - Compare similarity scores vs old model
   - Drop old `embedding` column (backup first)
   - Rename `embedding_new` → `embedding`

## Model Comparison

| Feature | all-MiniLM-L6-v2 (Old) | BGE-M3 (New) |
|---------|----------------------|--------------|
| **Dimensions** | 384 | 1024 |
| **Model Size** | 80MB | ~2.5GB |
| **Max Input Tokens** | 512 | 8,192 |
| **Languages** | English | 100+ |
| **Retrieval Modes** | Dense only | Dense + Sparse + Multi-vector |
| **MTEB Performance** | Mid-tier | Top-tier |
| **Quality** | Good | State-of-the-art |

## Expected Improvements

### 1. Better Similarity Scores
- More nuanced semantic understanding
- Better distinction between relevant/irrelevant chunks
- Higher quality top-k results

### 2. Longer Context Support
- Can handle 8K tokens vs 512 tokens
- Better for long PDF sections
- Improved technical documentation processing

### 3. Multilingual Capability
- Supports 100+ languages out of the box
- Better for mixed-language documents

### 4. Multi-functional Retrieval
- Dense embeddings (primary)
- Sparse embeddings (BM25-like)
- Multi-vector (ColBERT-like)

## Commands Reference

### Check Installation Status
```bash
tail -f /tmp/bge_install.log
```

### Test BGE-M3 Service
```bash
source venv/bin/activate
python3 << 'EOF'
from webapp.backend.services.embedding_service_bge import BGEEmbeddingService

service = BGEEmbeddingService()
service.load_model()

# Test single embedding
embedding = service.generate_embedding("test query")
print(f"Embedding dimension: {len(embedding)}")
print(f"✅ BGE-M3 working!")
EOF
```

### Run Re-embedding (When Ready)
```bash
source venv/bin/activate
python3 reembed_with_bge_m3.py
```

### Monitor Re-embedding Progress
```bash
# In separate terminal
watch -n 5 'PGPASSWORD=secure_rag_password_2024 psql -h localhost -U rag_user -d rag_database -c "SELECT COUNT(*) as completed FROM chunks WHERE embedding_new IS NOT NULL;"'
```

### Verify Results
```bash
PGPASSWORD=secure_rag_password_2024 psql -h localhost -U rag_user -d rag_database << 'EOF'
SELECT
    COUNT(*) FILTER (WHERE embedding IS NOT NULL) as old_embeddings,
    COUNT(*) FILTER (WHERE embedding_new IS NOT NULL) as new_embeddings,
    COUNT(*) as total_chunks
FROM chunks;
EOF
```

## Integration Steps (After Re-embedding)

### 1. Update document_service.py

Find this section in `webapp/backend/services/document_service.py`:

```python
# OLD (line ~1509)
distance = Chunk.embedding.cosine_distance(query_embedding)
```

Replace with:

```python
# NEW
distance = Chunk.embedding_new.cosine_distance(query_embedding)
```

Also update:
```python
# OLD (line ~1521)
Chunk.embedding.isnot(None)

# NEW
Chunk.embedding_new.isnot(None)
```

### 2. Update Embedding Service Import

In files that use embeddings, change:

```python
# OLD
from services.embedding_service import EmbeddingService
embedding_service = EmbeddingService()

# NEW
from services.embedding_service_bge import BGEEmbeddingService
embedding_service = BGEEmbeddingService(use_fp16=True)
```

### 3. Update Config

Update `core/config.py` or environment variables:

```python
# Add to Settings class
VECTOR_DIMENSION: int = 1024  # Changed from 384
EMBEDDING_MODEL: str = "BAAI/bge-m3"  # Changed from sentence-transformers/all-MiniLM-L6-v2
```

### 4. Restart Backend

```bash
# Stop old backend
pkill -f "python3 main.py"

# Start with new BGE-M3 service
cd webapp/backend
python3 main.py
```

## Rollback Plan (If Needed)

If BGE-M3 causes issues:

```bash
# Revert to old embeddings
PGPASSWORD=secure_rag_password_2024 psql -h localhost -U rag_user -d rag_database << 'EOF'
-- Drop new embeddings
ALTER TABLE chunks DROP COLUMN embedding_new;
ALTER TABLE chunks DROP COLUMN embedding_model_new;
DROP INDEX IF EXISTS idx_chunk_embedding_new;

-- Continue using old embedding column
-- No code changes needed if you haven't updated document_service.py yet
EOF
```

## Performance Benchmarks (To Be Filled)

After re-embedding, document performance here:

### Query Quality
- [ ] Test query: "give me example script"
  - Old model sources: ___ (similarity: ___)
  - BGE-M3 sources: ___ (similarity: ___)

- [ ] Test query: "Tell me everything about MaterialsScript"
  - Old model sources: ___ (similarity: ___)
  - BGE-M3 sources: ___ (similarity: ___)

### Processing Speed
- [ ] Re-embedding time: ___ minutes for 10,366 chunks
- [ ] Average speed: ___ chunks/second
- [ ] Query speed impact: ___ ms increase/decrease

## Troubleshooting

### Issue: Out of GPU Memory
**Solution:** Reduce batch size in `reembed_with_bge_m3.py`:
```python
batch_size = 8  # Instead of 12
```

### Issue: Slow Re-embedding
**Solution:** Check GPU usage:
```bash
nvidia-smi
watch -n 1 nvidia-smi
```

### Issue: Model Download Fails
**Solution:** Manually download model:
```bash
source venv/bin/activate
python3 -c "from FlagEmbedding import BGEM3FlagModel; BGEM3FlagModel('BAAI/bge-m3')"
```

## Support & References

- **BGE-M3 Docs:** https://github.com/FlagOpen/FlagEmbedding
- **Model Card:** https://huggingface.co/BAAI/bge-m3
- **MTEB Leaderboard:** https://huggingface.co/spaces/mteb/leaderboard

## Migration Checklist

- [x] Database schema updated
- [x] BGE-M3 service code created
- [x] Re-embedding script created
- [x] FlagEmbedding installed
- [x] BGE-M3 service tested
- [x] All chunks re-embedded
- [x] Search queries updated
- [x] Backend restarted
- [x] Material Studio expert prompt implemented
- [x] Documentation updated
- [ ] Query quality validated (ongoing)
- [ ] Old embeddings cleaned up (optional - when ready)

---

**Last Updated:** 2025-10-16
**Status:** ✅ COMPLETED
**Migration Duration:** 12.4 minutes for 10,366 chunks
**Next Action:** Monitor query quality and user feedback
