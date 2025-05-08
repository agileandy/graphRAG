"""
Database linkage module for GraphRAG project.

This module provides utilities for linking between the Neo4j graph database
and the vector database (ChromaDB).
"""
from typing import Dict, List, Any
from .neo4j_db import Neo4jDatabase
from .vector_db import VectorDatabase

class DatabaseLinkage:
    """
    Database linkage for GraphRAG project.
    """
    def __init__(self, neo4j_db: Neo4jDatabase, vector_db: VectorDatabase):
        """
        Initialize database linkage.
        
        Args:
            neo4j_db: Neo4j database instance
            vector_db: Vector database instance
        """
        self.neo4j_db = neo4j_db
        self.vector_db = vector_db
        
    def get_node_chunks(self, node_id: str, node_type: str) -> List[Dict[str, Any]]:
        """
        Get chunks from vector database for a specific Neo4j node.
        
        Args:
            node_id: Neo4j node ID
            node_type: Neo4j node type (e.g., 'Book', 'Chapter', 'Section', 'Concept')
            
        Returns:
            List of chunks with their metadata and embeddings
        """
        # Convert node type to lowercase for metadata field name
        node_type_lower = node_type.lower()
        
        # Query vector database for chunks related to this node
        results = self.vector_db.get(
            where={f"{node_type_lower}_id": node_id}
        )
        
        return {
            "ids": results.get("ids", []),
            "documents": results.get("documents", []),
            "metadatas": results.get("metadatas", []),
            "embeddings": results.get("embeddings", [])
        }
        
    def get_related_nodes(self, chunk_id: str) -> List[Dict[str, Any]]:
        """
        Get Neo4j nodes related to a specific chunk in the vector database.
        
        Args:
            chunk_id: Vector database chunk ID
            
        Returns:
            List of related Neo4j nodes
        """
        # Get chunk metadata from vector database
        chunk_data = self.vector_db.get(ids=[chunk_id])
        
        if not chunk_data.get("ids"):
            return []
            
        # Extract node IDs from metadata
        metadata = chunk_data["metadatas"][0]
        related_nodes = []
        
        # Query Neo4j for each related node
        for node_type in ["book", "chapter", "section", "concept"]:
            node_id = metadata.get(f"{node_type}_id")
            if node_id:
                # Capitalize node type for Neo4j label
                node_type_cap = node_type.capitalize()
                
                try:
                    # Query Neo4j for node details
                    query = f"""
                    MATCH (n:{node_type_cap} {{id: $node_id}})
                    RETURN n.id AS id, n.title AS title, n.name AS name, labels(n)[0] AS type
                    """
                    
                    records = self.neo4j_db.run_query(query, {"node_id": node_id})
                    
                    for record in records:
                        # Get name or title
                        name = record.get("name") or record.get("title") or "Unnamed"
                        
                        related_nodes.append({
                            "id": record["id"],
                            "type": record["type"],
                            "name": name
                        })
                except Exception as e:
                    print(f"Error querying Neo4j for node {node_id}: {e}")
                    
        return related_nodes
        
    def hybrid_search(self, 
                     query_text: str, 
                     n_vector_results: int = 5,
                     max_graph_hops: int = 2) -> Dict[str, Any]:
        """
        Perform hybrid search using both vector and graph databases.
        
        Args:
            query_text: Query text
            n_vector_results: Number of initial vector results
            max_graph_hops: Maximum number of hops in the graph
            
        Returns:
            Combined search results
        """
        # 1. First, query the vector database
        vector_results = self.vector_db.query(
            query_texts=[query_text],
            n_results=n_vector_results
        )
        
        # 2. For each vector result, find related nodes in Neo4j
        # Use a dictionary to deduplicate results by concept ID
        graph_results_dict = {}
        
        for i, chunk_id in enumerate(vector_results.get("ids", [[]])[0]):
            # Get metadata for this chunk
            metadata = vector_results["metadatas"][0][i]
            
            # Find concept nodes mentioned in this chunk
            concept_id = metadata.get("concept_id")
            if concept_id:
                try:
                    # Query Neo4j for related concepts within max_graph_hops
                    query = f"""
                    MATCH (c:Concept {{id: $concept_id}})-[r:RELATED_TO*1..{max_graph_hops}]-(related:Concept)
                    RETURN related.id AS id, related.name AS name, 
                           reduce(s = 0, rel IN r | s + coalesce(rel.strength, 0.5)) AS relevance_score
                    ORDER BY relevance_score DESC
                    """
                    
                    records = self.neo4j_db.run_query(query, {"concept_id": concept_id})
                    
                    for record in records:
                        related_id = record["id"]
                        # Only add if not already in results or if new score is higher
                        if (related_id not in graph_results_dict or 
                            record["relevance_score"] > graph_results_dict[related_id]["relevance_score"]):
                            graph_results_dict[related_id] = {
                                "id": related_id,
                                "name": record["name"],
                                "relevance_score": record["relevance_score"],
                                "source": "graph"
                            }
                except Exception as e:
                    print(f"Error querying Neo4j for related concepts: {e}")
        
        # Convert dictionary to list and sort by relevance score
        graph_results = list(graph_results_dict.values())
        graph_results.sort(key=lambda x: -x["relevance_score"])
        
        # 3. Combine results
        combined_results = {
            "vector_results": {
                "ids": vector_results.get("ids", [[]])[0],
                "documents": vector_results.get("documents", [[]])[0],
                "metadatas": vector_results.get("metadatas", [[]])[0],
                "distances": vector_results.get("distances", [[]])[0] if "distances" in vector_results else [],
            },
            "graph_results": graph_results
        }
        
        return combined_results