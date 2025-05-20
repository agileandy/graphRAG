# Database Optimizations for GraphRAG

This document outlines the database optimizations implemented in the GraphRAG system to handle large volumes of data (1,100+ ebooks, ~70M words).

## Neo4j Optimizations

### Memory Configuration

The Neo4j memory settings have been optimized for better performance with large knowledge graphs:

```
dbms.memory.heap.initial_size=1024m  # Increased from 512m
dbms.memory.heap.max_size=2048m      # Increased from 1024m
dbms.memory.pagecache.size=1024m     # Increased from 512m
dbms.memory.transaction.total.max=512m
db.memory.transaction.max=64m
```

These settings provide a good balance between performance and memory usage. Adjust these values based on your available system resources.

### Additional Indexes

Additional indexes have been added to improve query performance:

```cypher
// Book indexes
CREATE INDEX book_title IF NOT EXISTS FOR (b:Book) ON (b.title)
CREATE INDEX book_category IF NOT EXISTS FOR (b:Book) ON (b.category)
CREATE INDEX book_isbn IF NOT EXISTS FOR (b:Book) ON (b.isbn)

// Chapter indexes
CREATE INDEX chapter_title IF NOT EXISTS FOR (c:Chapter) ON (c.title)
CREATE INDEX chapter_book_id IF NOT EXISTS FOR (c:Chapter) ON (c.book_id)

// Section indexes
CREATE INDEX section_title IF NOT EXISTS FOR (s:Section) ON (s.title)
CREATE INDEX section_chapter_id IF NOT EXISTS FOR (s:Section) ON (s.chapter_id)

// Concept indexes
CREATE INDEX concept_name IF NOT EXISTS FOR (c:Concept) ON (c.name)
CREATE INDEX concept_category IF NOT EXISTS FOR (c:Concept) ON (c.category)
```

These indexes significantly improve the performance of common queries, especially for large datasets.

## Vector Database (ChromaDB) Optimizations

### HNSW Index Configuration

The HNSW (Hierarchical Navigable Small World) index parameters have been optimized for large datasets:

```python
collection_metadata = {
    "hnsw:space": "cosine",          # Use cosine similarity
    "hnsw:construction_ef": 128,     # Default is 100
    "hnsw:search_ef": 128,           # Default is 10
    "hnsw:M": 16,                    # Default is 16
    "hnsw:num_threads": 4            # Use multiple threads for indexing
}
```

These settings provide a good balance between search accuracy and performance.

### Smart Chunking Strategy

A smart chunking strategy has been implemented to improve the quality of vector search results:

- Uses semantic boundaries (paragraphs, sentences) for more natural chunks
- Implements proper overlap between chunks to maintain context
- Handles large documents efficiently

Example usage:

```python
from src.processing.document_processor import smart_chunk_text

chunks = smart_chunk_text(
    text=document_text,
    chunk_size=1000,
    overlap=200,
    semantic_boundaries=True
)
```

### Batch Processing

Batch processing has been implemented to efficiently handle large volumes of data:

```python
from src.database.vector_db import VectorDatabase

vector_db = VectorDatabase()
vector_db.add_documents(
    documents=documents,
    metadatas=metadatas,
    ids=ids,
    batch_size=100  # Process in batches of 100
)
```

The default batch size is 100, which provides a good balance between performance and memory usage. Adjust this value based on your system resources and document sizes.

### Metadata Optimization

Metadata optimization has been implemented to improve filtering performance:

```python
from src.processing.document_processor import optimize_metadata

optimized_metadata = optimize_metadata(metadata)
```

This function:
- Converts lists to comma-separated strings (ChromaDB limitation)
- Flattens nested dictionaries
- Adds searchable lowercase versions of key text fields

## New Optimized Scripts

### Optimized Document Addition

The `scripts/optimized_add_document.py` script provides an optimized way to add documents to the GraphRAG system:

```bash
python scripts/optimized_add_document.py --file path/to/document.txt --chunk-size 1000 --overlap 200 --batch-size 100
```

### Data Optimization

The `scripts/optimize_existing_data.py` script optimizes existing data in the vector database:

```bash
python scripts/optimize_existing_data.py --chunk-size 1000 --overlap 200 --batch-size 100
```

Use the `--dry-run` flag to see what would be changed without actually modifying the database.

## Performance Considerations

### Memory Usage

The optimized settings are designed to work well on systems with at least 4GB of RAM. If you have less memory available, consider reducing the following:

- Neo4j heap size (`dbms.memory.heap.max_size`)
- Neo4j page cache size (`dbms.memory.pagecache.size`)
- Batch size for vector database operations

### Disk Space

The optimized chunking strategy may increase the total number of chunks, which will increase disk space usage. Make sure you have sufficient disk space available.

### Processing Time

The optimized settings prioritize search quality and accuracy over processing speed. Initial document ingestion may be slower, but query performance will be significantly improved.

## Monitoring and Tuning

Monitor the performance of your GraphRAG system and adjust the optimization parameters as needed:

- If you experience memory errors, reduce batch sizes and memory settings
- If search results are not accurate enough, increase HNSW parameters
- If processing is too slow, consider increasing batch sizes or reducing chunk overlap

Use the Neo4j Browser to monitor query performance and identify slow queries that may need further optimization.
