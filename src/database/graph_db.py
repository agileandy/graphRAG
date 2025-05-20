"""Graph database wrapper for GraphRAG project.

This module provides a unified interface for graph database operations,
currently implemented using Neo4j.
"""

import logging
import uuid
from datetime import datetime
from typing import Any

from src.database.neo4j_db import Neo4jDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GraphDatabase:
    """Graph database wrapper for GraphRAG project.

    This class provides a unified interface for graph database operations,
    abstracting away the underlying implementation (currently Neo4j).
    """

    def __init__(
        self,
        uri: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        """Initialize graph database connection.

        Args:
            uri: Database URI (default: from environment variable)
            username: Database username (default: from environment variable)
            password: Database password (default: from environment variable)

        """
        self.neo4j_db = Neo4jDatabase(uri, username, password)

    def connect(self) -> None:
        """Connect to the graph database."""
        self.neo4j_db.connect()

    def close(self) -> None:
        """Close the graph database connection."""
        self.neo4j_db.close()

    def verify_connection(self) -> bool:
        """Verify graph database connection.

        Returns:
            True if connection is successful, False otherwise

        """
        return self.neo4j_db.verify_connection()

    def create_schema(self) -> None:
        """Create initial graph database schema."""
        self.neo4j_db.create_schema()

    def clear_database(self) -> None:
        """Clear all data from the database.
        WARNING: This will delete all nodes and relationships.
        """
        self.neo4j_db.clear_database()

    def create_dummy_data(self) -> None:
        """Create dummy data for testing."""
        self.neo4j_db.create_dummy_data()

    def add_document(
        self, document_id: str, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """Add a document to the graph database.

        Args:
            document_id: Document ID
            metadata: Document metadata

        Returns:
            Dictionary with document node information

        """
        # Prepare metadata
        properties = {
            "id": document_id,
            "title": metadata.get("title", "Untitled Document"),
            "created_at": datetime.now().isoformat(),
        }

        # Add optional metadata fields if present
        for field in [
            "author",
            "source",
            "url",
            "publication_date",
            "category",
            "tags",
        ]:
            if field in metadata:
                properties[field] = metadata[field]

        # Create document node
        query = """
        CREATE (d:Document $properties)
        RETURN d.id AS id, d.title AS title
        """

        result = self.neo4j_db.run_query_and_return_single(
            query, {"properties": properties}
        )

        return result

    def add_concept(
        self, concept_name: str, properties: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Add a concept to the graph database.

        Args:
            concept_name: Concept name
            properties: Additional concept properties

        Returns:
            Dictionary with concept node information

        """
        # Generate concept ID if not provided
        concept_properties = properties or {}
        if "id" not in concept_properties:
            concept_properties["id"] = f"concept-{uuid.uuid4()}"

        concept_properties["name"] = concept_name
        concept_properties["created_at"] = datetime.now().isoformat()

        # Check if concept already exists (case-insensitive match)
        query = """
        MATCH (c:Concept)
        WHERE toLower(c.name) = toLower($name)
        RETURN c.id AS id, c.name AS name
        """

        existing = self.neo4j_db.run_query_and_return_single(
            query, {"name": concept_name}
        )

        if existing:
            logger.debug(
                f"Concept '{concept_name}' already exists with ID {existing['id']}"
            )
            return existing

        # Create concept node
        query = """
        CREATE (c:Concept $properties)
        RETURN c.id AS id, c.name AS name
        """

        result = self.neo4j_db.run_query_and_return_single(
            query, {"properties": concept_properties}
        )

        return result

    def add_document_concept_relationship(
        self,
        document_id: str,
        concept_id: str,
        relationship_type: str = "MENTIONS",
        properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Add a relationship between a document and a concept.

        Args:
            document_id: Document ID
            concept_id: Concept ID
            relationship_type: Type of relationship
            properties: Relationship properties

        Returns:
            Dictionary with relationship information

        """
        rel_properties = properties or {}
        rel_properties["created_at"] = datetime.now().isoformat()

        # Create relationship
        query = f"""
        MATCH (d:Document {{id: $document_id}})
        MATCH (c:Concept {{id: $concept_id}})
        MERGE (d)-[r:{relationship_type}]->(c)
        ON CREATE SET r = $properties
        RETURN d.id AS document_id, c.id AS concept_id, type(r) AS relationship_type
        """

        result = self.neo4j_db.run_query_and_return_single(
            query,
            {
                "document_id": document_id,
                "concept_id": concept_id,
                "properties": rel_properties,
            },
        )

        return result

    def add_concept_relationship(
        self,
        source_concept: str,
        target_concept: str,
        relationship_type: str = "RELATED_TO",
        properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Add a relationship between two concepts.

        Args:
            source_concept: Source concept name or ID
            target_concept: Target concept name or ID
            relationship_type: Type of relationship
            properties: Relationship properties

        Returns:
            Dictionary with relationship information

        """
        rel_properties = properties or {}
        rel_properties["created_at"] = datetime.now().isoformat()

        # Set default strength if not provided
        if "strength" not in rel_properties:
            rel_properties["strength"] = 0.5

        # Determine if source and target are IDs or names
        source_is_id = source_concept.startswith("concept-")
        target_is_id = target_concept.startswith("concept-")

        # Create relationship based on whether inputs are IDs or names
        if source_is_id and target_is_id:
            query = f"""
            MATCH (source:Concept {{id: $source}})
            MATCH (target:Concept {{id: $target}})
            MERGE (source)-[r:{relationship_type}]->(target)
            ON CREATE SET r = $properties
            RETURN source.id AS source_id, source.name AS source_name,
                   target.id AS target_id, target.name AS target_name,
                   type(r) AS relationship_type
            """
            params = {
                "source": source_concept,
                "target": target_concept,
                "properties": rel_properties,
            }
        elif source_is_id:
            query = f"""
            MATCH (source:Concept {{id: $source}})
            MATCH (target:Concept)
            WHERE toLower(target.name) = toLower($target)
            MERGE (source)-[r:{relationship_type}]->(target)
            ON CREATE SET r = $properties
            RETURN source.id AS source_id, source.name AS source_name,
                   target.id AS target_id, target.name AS target_name,
                   type(r) AS relationship_type
            """
            params = {
                "source": source_concept,
                "target": target_concept,
                "properties": rel_properties,
            }
        elif target_is_id:
            query = f"""
            MATCH (source:Concept)
            WHERE toLower(source.name) = toLower($source)
            MATCH (target:Concept {{id: $target}})
            MERGE (source)-[r:{relationship_type}]->(target)
            ON CREATE SET r = $properties
            RETURN source.id AS source_id, source.name AS source_name,
                   target.id AS target_id, target.name AS target_name,
                   type(r) AS relationship_type
            """
            params = {
                "source": source_concept,
                "target": target_concept,
                "properties": rel_properties,
            }
        else:
            # Both are names, need to find or create both concepts
            query = f"""
            MERGE (source:Concept {{name: $source}})
            ON CREATE SET source.id = $source_id, source.created_at = $created_at

            MERGE (target:Concept {{name: $target}})
            ON CREATE SET target.id = $target_id, target.created_at = $created_at

            MERGE (source)-[r:{relationship_type}]->(target)
            ON CREATE SET r = $properties

            RETURN source.id AS source_id, source.name AS source_name,
                   target.id AS target_id, target.name AS target_name,
                   type(r) AS relationship_type
            """
            params = {
                "source": source_concept,
                "target": target_concept,
                "source_id": f"concept-{uuid.uuid4()}",
                "target_id": f"concept-{uuid.uuid4()}",
                "created_at": datetime.now().isoformat(),
                "properties": rel_properties,
            }

        result = self.neo4j_db.run_query_and_return_single(query, params)

        return result

    def get_concept_by_name(self, concept_name: str) -> list[dict[str, Any]]:
        """Get concepts by name (partial match).

        Args:
            concept_name: Concept name to search for

        Returns:
            List of matching concepts

        """
        query = """
        MATCH (c:Concept)
        WHERE toLower(c.name) CONTAINS toLower($name)
        RETURN c.id AS id, c.name AS name, c.type AS type, c.description AS description
        ORDER BY size(c.name) ASC
        LIMIT 10
        """

        results = self.neo4j_db.run_query(query, {"name": concept_name})

        return results

    def get_related_concepts(
        self, concept_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get concepts related to a given concept.

        Args:
            concept_id: Concept ID
            limit: Maximum number of related concepts to return

        Returns:
            List of related concepts

        """
        query = f"""
        MATCH (c:Concept {{id: $concept_id}})-[r:RELATED_TO]-(related:Concept)
        RETURN related.id AS id, related.name AS name,
               related.type AS type, related.description AS description,
               r.strength AS strength, r.description AS relationship_description
        ORDER BY r.strength DESC
        LIMIT {limit}
        """

        results = self.neo4j_db.run_query(query, {"concept_id": concept_id})

        return results

    def get_documents_by_concept(
        self, concept_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get documents related to a given concept.

        Args:
            concept_id: Concept ID
            limit: Maximum number of documents to return

        Returns:
            List of related documents

        """
        query = f"""
        MATCH (d:Document)-[r:MENTIONS]->(c:Concept {{id: $concept_id}})
        RETURN d.id AS id, d.title AS title, d.author AS author, d.source AS source
        LIMIT {limit}
        """

        results = self.neo4j_db.run_query(query, {"concept_id": concept_id})

        return results

    def get_concept_count(self) -> int:
        """Get the count of concept nodes in the database.

        Returns:
            Number of concept nodes

        """
        query = "MATCH (c:Concept) RETURN count(c) AS count"
        result = self.neo4j_db.run_query_and_return_single(query)
        return result.get("count", 0)

    def get_document_count(self) -> int:
        """Get the count of document nodes in the database.

        Returns:
            Number of document nodes

        """
        query = "MATCH (d:Document) RETURN count(d) AS count"
        result = self.neo4j_db.run_query_and_return_single(query)
        return result.get("count", 0)

    def get_relationship_count(self) -> int:
        """Get the count of relationships in the database.

        Returns:
            Number of relationships

        """
        query = "MATCH ()-[r]->() RETURN count(r) AS count"
        result = self.neo4j_db.run_query_and_return_single(query)
        return result.get("count", 0)
