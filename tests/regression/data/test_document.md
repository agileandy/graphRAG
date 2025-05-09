# GraphRAG: Enhancing Large Language Models with Knowledge Graphs

GraphRAG is an innovative approach that combines Retrieval-Augmented Generation (RAG) 
with knowledge graphs to enhance the capabilities of Large Language Models (LLMs).

## Traditional RAG vs. GraphRAG

Traditional RAG systems use vector databases to retrieve relevant information based on 
semantic similarity. While effective, this approach lacks the ability to capture 
relationships between concepts.

GraphRAG addresses this limitation by integrating a knowledge graph (Neo4j) with a 
vector database (ChromaDB). This hybrid approach enables:

1. Semantic search through vector embeddings
2. Relationship-aware retrieval through graph traversal
3. Enhanced context by combining both retrieval methods

## System Architecture

The system extracts entities and relationships from documents, stores them in both 
databases, and provides a unified query interface that leverages the strengths of both 
approaches.

## Benefits

GraphRAG can significantly improve the accuracy and relevance of LLM responses by 
providing both textual context and structural knowledge about the relationships 
between concepts.