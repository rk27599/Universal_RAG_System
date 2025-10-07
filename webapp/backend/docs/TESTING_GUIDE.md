# Testing the Vector Search Optimization

## ✅ Services Status

Both services are now running:

- **Backend**: http://127.0.0.1:8000 (FastAPI)
- **Frontend**: http://localhost:3000 (React)

## 🧪 How to Test the Vector Search Optimization

### Method 1: Web UI Testing (Recommended for Visual Testing)

1. **Open the application**:
   ```
   http://localhost:3000
   ```

2. **Login or Register** a test account

3. **Upload some documents**:
   - Go to "Documents" tab
   - Upload 5-10 HTML or text files
   - Wait for processing to complete (you'll see progress)

4. **Test the search**:
   - Go to "Chat" tab
   - Create a new conversation
   - Ask questions about your uploaded documents
   - The system will now use the optimized vector search!

5. **Check the backend logs** to see the optimization in action:
   ```bash
   # In the terminal, watch the backend output for:
   🔍 Vector search: query_embedding dimensions=384, top_k=5, min_similarity=0.3
   📊 Executing vector similarity search with HNSW index...
   ✅ Found X results above threshold 0.3
   ```

### Method 2: API Testing (Recommended for Performance Testing)

#### Step 1: Get an authentication token

```bash
# Register a user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPassword123!"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "TestPassword123!"
  }'

# Copy the "access_token" from the response
```

#### Step 2: Upload test documents

```bash
# Upload an HTML file
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/your/document.html"

# Check upload status
curl -X GET http://localhost:8000/api/documents \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Step 3: Test vector search

```bash
# Search with the optimized function
curl -X POST http://localhost:8000/api/documents/search \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the main topic of the document?",
    "topK": 5,
    "minSimilarity": 0.3
  }'
```

**Watch the backend terminal** - you should see:
```
🔍 Vector search: query_embedding dimensions=384, top_k=5, min_similarity=0.3
📊 Executing vector similarity search with HNSW index...
✅ Found 5 results above threshold 0.3
  Result 1: chunk_id=123, similarity=0.8521, preview=...
  Result 2: chunk_id=456, similarity=0.7843, preview=...
  Result 3: chunk_id=789, similarity=0.6932, preview=...
```

### Method 3: Performance Benchmark

Run the included benchmark to see theoretical performance:

```bash
cd /home/rkpatel/RAG/webapp/backend
python3 tests/test_vector_search_performance.py
```

You should see output like:
```
Chunks     | Old (Python)    | New (pgvector)  | Speedup
-----------|-----------------|-----------------|----------
100        |       0.0015s   |       0.0116s   |    0.1x
10,000     |       0.1024s   |       0.0183s   |    5.6x
100,000    |       1.0835s   |       0.0216s   |   50.1x

✅ Average speedup: 12.2x faster
```

### Method 4: Database Query Analysis

Monitor actual PostgreSQL performance:

```bash
# Connect to your PostgreSQL database
psql -U your_user -d your_database

# Enable query timing
\timing

# Run a manual vector search query
EXPLAIN ANALYZE
SELECT
    chunks.id,
    chunks.content,
    1 - (chunks.embedding <=> '[0.1, 0.2, ...]'::vector) / 2 AS similarity
FROM chunks
JOIN documents ON chunks.document_id = documents.id
WHERE
    documents.user_id = 1
    AND chunks.embedding IS NOT NULL
    AND (chunks.embedding <=> '[0.1, 0.2, ...]'::vector) <= 1.4
ORDER BY chunks.embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 5;

# Look for "Index Scan using idx_chunk_embedding" in the output
# This confirms the HNSW index is being used
```

## 🔍 What to Look For

### Backend Logs (Optimized Version)
```
INFO: 🔍 Vector search: query_embedding dimensions=384, top_k=5, min_similarity=0.3
INFO: 📊 Executing vector similarity search with HNSW index...
INFO: ✅ Found 5 results above threshold 0.3
INFO:   Result 1: chunk_id=123, similarity=0.8521, preview=...
```

### Performance Indicators

**Old Implementation** (if you had it):
- Logs: "Computing similarities for 10000 chunks..."
- Time: Several seconds for large datasets
- Memory: High RAM usage

**New Implementation** (current):
- Logs: "Executing vector similarity search with HNSW index..."
- Time: Milliseconds even for large datasets
- Memory: Minimal - only top_k results loaded

### Success Indicators

✅ **Query completes in < 100ms** even with thousands of chunks
✅ **Backend shows "HNSW index" in logs**
✅ **Search results are accurate and relevant**
✅ **No "Computing similarities" loop in logs**
✅ **Memory usage stays low during searches**

## 📊 Performance Comparison

### Before Optimization
```python
# Loaded ALL chunks
all_chunks = query_builder.all()

# Python loop - O(n) complexity
for chunk, document in all_chunks:
    similarity = compute_similarity(...)
    if similarity >= threshold:
        results.append(...)

# Sort and return top_k
results.sort(...)
return results[:top_k]
```

**Performance**: 1+ second for 100K chunks

### After Optimization
```python
# PostgreSQL does all the work - O(log n) complexity
distance = Chunk.embedding.cosine_distance(query_embedding)

results = query_builder\
    .filter(distance <= max_distance)\
    .order_by(distance)\
    .limit(top_k)\
    .all()
```

**Performance**: ~20ms for 100K chunks (50x faster!)

## 🐛 Troubleshooting

### Issue: "HNSW index not being used"

**Check**:
```sql
-- Verify index exists
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'chunks';

-- Should show: idx_chunk_embedding with "vector_cosine_ops"
```

**Fix**: Run the migration:
```bash
cd /home/rkpatel/RAG/webapp/backend
alembic revision -m "optimize_vector_index"
# Edit migration file to recreate index with operator class
alembic upgrade head
```

### Issue: "Slow queries still"

**Check**:
```sql
-- Analyze table statistics
ANALYZE chunks;

-- Check query plan
EXPLAIN ANALYZE
SELECT ... ORDER BY embedding <=> query_vector LIMIT 5;
```

**Tune**:
```sql
-- Increase search quality
SET hnsw.ef_search = 100;

-- Increase memory for queries
SET work_mem = '256MB';
```

### Issue: "No results returned"

**Check**:
1. Embeddings exist: `SELECT COUNT(*) FROM chunks WHERE embedding IS NOT NULL;`
2. Threshold is not too high: Try `minSimilarity: 0.1` instead of `0.3`
3. Documents are processed: Check `processing_status = 'completed'`

## 📈 Monitoring Performance

### Real-time Monitoring

Watch backend logs:
```bash
# Terminal 1: Backend
cd /home/rkpatel/RAG/webapp/backend
python3 main.py

# Terminal 2: Follow logs
tail -f logs/app.log | grep "Vector search"
```

### PostgreSQL Statistics

```sql
-- Enable pg_stat_statements
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- View vector search performance
SELECT
    query,
    calls,
    mean_exec_time,
    max_exec_time,
    stddev_exec_time
FROM pg_stat_statements
WHERE query LIKE '%cosine_distance%'
ORDER BY mean_exec_time DESC
LIMIT 10;
```

## 🎯 Expected Results

For a well-indexed database with 10,000+ chunks:

| Metric | Value |
|--------|-------|
| Query Time | < 50ms |
| Memory Usage | < 10MB |
| CPU Usage | < 5% |
| Results Accuracy | High (>0.7 similarity for relevant chunks) |
| Index Type | HNSW with vector_cosine_ops |

## 🚀 Next Steps After Testing

1. **Monitor production performance** with real queries
2. **Tune parameters** if needed:
   - Increase `ef_search` for better recall
   - Adjust `m` and `ef_construction` for index quality
3. **Scale up** - the optimization handles millions of chunks efficiently
4. **Add monitoring** - track query times and index performance

## 📝 Notes

- The optimization is **backward compatible** - no API changes needed
- Falls back to TF-IDF if embeddings are unavailable
- Works with existing HNSW index configuration
- No external dependencies - pure PostgreSQL pgvector

---

**Current Status**: ✅ Both services running and ready to test!

- Backend: http://127.0.0.1:8000
- Frontend: http://localhost:3000

Start testing by uploading documents and running searches! 🎉
