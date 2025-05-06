"""
Vector database connection and operations for GraphRAG project.
"""
import os
from typing import Dict, List, Optional, Any, Union
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VectorDatabase:
    """
    Vector database connection and operations for GraphRAG project.
    """
    def __init__(self, persist_directory: Optional[str] = None):
        """
        Initialize vector database connection.
        
        Args:
            persist_directory: Directory to persist vector database
                (default: from environment variable)
        """
        self.persist_directory = persist_directory or os.getenv(
            "CHROMA_PERSIST_DIRECTORY", "./data/chromadb"
        )
        self.client = None
        self.collection = None
        
    def connect(self, collection_name: str = "ebook_chunks") -> None:
        """
        Connect to vector database and get or create collection.
        
        Args:
            collection_name: Name of the collection to use
        """
        # Ensure the persist directory exists
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Create client with persistence using the new client format
        self.client = chromadb.PersistentClient(
            path=self.persist_directory
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
    def verify_connection(self) -> bool:
        """
        Verify vector database connection.
        
        Returns:
            True if connection is successful, False otherwise.
        """
        try:
            self.connect()
            # Check if we can get collection info
            self.collection.count()
            return True
        except Exception as e:
            print(f"Vector database connection error: {e}")
            return False
            
    def add_documents(self, 
                     documents: List[str], 
                     embeddings: Optional[List[List[float]]] = None,
                     metadatas: Optional[List[Dict[str, Any]]] = None,
                     ids: Optional[List[str]] = None) -> None:
        """
        Add documents to vector database.
        
        Args:
            documents: List of document texts
            embeddings: List of document embeddings (optional)
            metadatas: List of document metadata (optional)
            ids: List of document IDs (optional)
        """
        if self.collection is None:
            self.connect()
            
        # Generate IDs if not provided
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]
            
        # Add documents
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
    def query(self, 
             query_texts: Optional[List[str]] = None,
             query_embeddings: Optional[List[List[float]]] = None,
             n_results: int = 5,
             where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Query vector database.
        
        Args:
            query_texts: List of query texts
            query_embeddings: List of query embeddings
            n_results: Number of results to return
            where: Filter query by metadata
            
        Returns:
            Query results
        """
        if self.collection is None:
            self.connect()
            
        return self.collection.query(
            query_texts=query_texts,
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where
        )
        
    def get(self, 
           ids: Optional[List[str]] = None,
           where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get documents from vector database.
        
        Args:
            ids: List of document IDs
            where: Filter query by metadata
            
        Returns:
            Documents
        """
        if self.collection is None:
            self.connect()
            
        return self.collection.get(
            ids=ids,
            where=where
        )
        
    def count(self) -> int:
        """
        Count documents in vector database.
        
        Returns:
            Number of documents
        """
        if self.collection is None:
            self.connect()
            
        return self.collection.count()
        
    def create_dummy_data(self) -> None:
        """
        Create dummy data for testing.
        """
        if self.collection is None:
            self.connect()
            
        # Create some dummy documents with metadata linking to Neo4j nodes
        documents = [
            "Neural networks are a set of algorithms, modeled loosely after the human brain, that are designed to recognize patterns.",
            "Decision trees are a non-parametric supervised learning method used for classification and regression.",
            "Gradient descent is an optimization algorithm used to minimize some function by iteratively moving in the direction of steepest descent."
        ]
        
        # Metadata linking to Neo4j nodes
        metadatas = [
            {
                "book_id": "book-001",
                "chapter_id": "chapter-001",
                "section_id": "section-001",
                "concept_id": "concept-001",
                "title": "Neural Networks",
                "source": "Introduction to Machine Learning"
            },
            {
                "book_id": "book-001",
                "chapter_id": "chapter-001",
                "section_id": "section-001",
                "concept_id": "concept-002",
                "title": "Decision Trees",
                "source": "Introduction to Machine Learning"
            },
            {
                "book_id": "book-001",
                "chapter_id": "chapter-001",
                "section_id": "section-002",
                "concept_id": "concept-003",
                "title": "Gradient Descent",
                "source": "Introduction to Machine Learning"
            }
        ]
        
        # IDs matching Neo4j node IDs for concepts
        ids = ["chunk-concept-001", "chunk-concept-002", "chunk-concept-003"]
        
        # Add documents
        self.add_documents(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )