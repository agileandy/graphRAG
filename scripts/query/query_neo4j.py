#!/usr/bin/env python3
"""
Script to directly query Neo4j in the GraphRAG system.
"""

import json
import argparse
import sys
import os
from neo4j import GraphDatabase

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config import get_port

# Get Neo4j port from centralized configuration
neo4j_port = get_port('neo4j_bolt')
docker_neo4j_port = get_port('docker_neo4j_bolt')

# Default Neo4j connection settings
DEFAULT_URI = f"bolt://localhost:{docker_neo4j_port}"  # Default to Docker port mapping
DEFAULT_USERNAME = "neo4j"
DEFAULT_PASSWORD = "graphrag"

class Neo4jQuerier:
    """Class to query Neo4j database."""

    def __init__(self, uri, username, password):
        """Initialize the Neo4j connection."""
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        """Close the Neo4j connection."""
        self.driver.close()

    def test_connection(self):
        """Test the Neo4j connection."""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 'Connection successful' AS message")
                record = result.single()
                return record["message"]
        except Exception as e:
            return f"Connection failed: {e}"

    def get_node_count(self):
        """Get the count of nodes in the database."""
        with self.driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) AS count")
            record = result.single()
            return record["count"]

    def get_relationship_count(self):
        """Get the count of relationships in the database."""
        with self.driver.session() as session:
            result = session.run("MATCH ()-[r]->() RETURN count(r) AS count")
            record = result.single()
            return record["count"]

    def get_concept_count(self):
        """Get the count of concept nodes in the database."""
        with self.driver.session() as session:
            result = session.run("MATCH (c:Concept) RETURN count(c) AS count")
            record = result.single()
            return record["count"]

    def get_document_count(self):
        """Get the count of document nodes in the database."""
        with self.driver.session() as session:
            result = session.run("MATCH (d:Document) RETURN count(d) AS count")
            record = result.single()
            return record["count"]

    def get_all_concepts(self):
        """Get all concept nodes in the database."""
        with self.driver.session() as session:
            result = session.run("MATCH (c:Concept) RETURN c.name AS name, c.id AS id")
            return [{"name": record["name"], "id": record["id"]} for record in result]

    def get_concept_by_name(self, name):
        """Get a concept node by name."""
        with self.driver.session() as session:
            result = session.run(
                "MATCH (c:Concept) WHERE c.name CONTAINS $name RETURN c.name AS name, c.id AS id",
                name=name
            )
            return [{"name": record["name"], "id": record["id"]} for record in result]

    def get_related_concepts(self, concept_id):
        """Get concepts related to a given concept."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (c1:Concept {id: $concept_id})-[r:RELATED_TO]-(c2:Concept)
                RETURN c2.name AS name, c2.id AS id, r.weight AS weight
                ORDER BY r.weight DESC
                """,
                concept_id=concept_id
            )
            return [{"name": record["name"], "id": record["id"], "weight": record["weight"]}
                    for record in result]

    def get_documents_by_concept(self, concept_id, limit=10):
        """Get documents related to a given concept."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (c:Concept {id: $concept_id})-[:MENTIONED_IN]->(d:Document)
                RETURN d.title AS title, d.id AS id
                LIMIT $limit
                """,
                concept_id=concept_id, limit=limit
            )
            return [{"title": record["title"], "id": record["id"]} for record in result]

    def run_custom_query(self, query):
        """Run a custom Cypher query."""
        with self.driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]

def main():
    parser = argparse.ArgumentParser(description="Query Neo4j in the GraphRAG system")
    parser.add_argument("--uri", default=DEFAULT_URI, help="Neo4j URI")
    parser.add_argument("--username", default=DEFAULT_USERNAME, help="Neo4j username")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Neo4j password")
    parser.add_argument("--test", action="store_true", help="Test the Neo4j connection")
    parser.add_argument("--counts", action="store_true", help="Get counts of nodes and relationships")
    parser.add_argument("--concepts", action="store_true", help="Get all concepts")
    parser.add_argument("--concept", help="Get a concept by name")
    parser.add_argument("--related", help="Get concepts related to a given concept ID")
    parser.add_argument("--documents", help="Get documents related to a given concept ID")
    parser.add_argument("--query", help="Run a custom Cypher query")
    args = parser.parse_args()

    # Create Neo4j querier
    querier = Neo4jQuerier(args.uri, args.username, args.password)

    try:
        # Test connection
        if args.test:
            message = querier.test_connection()
            print(f"Connection test: {message}")

        # Get counts
        if args.counts:
            node_count = querier.get_node_count()
            relationship_count = querier.get_relationship_count()
            concept_count = querier.get_concept_count()
            document_count = querier.get_document_count()

            print(f"Node count: {node_count}")
            print(f"Relationship count: {relationship_count}")
            print(f"Concept count: {concept_count}")
            print(f"Document count: {document_count}")

        # Get all concepts
        if args.concepts:
            concepts = querier.get_all_concepts()
            print(f"Found {len(concepts)} concepts:")
            for concept in concepts:
                print(f"  - {concept['name']} (ID: {concept['id']})")

        # Get concept by name
        if args.concept:
            concepts = querier.get_concept_by_name(args.concept)
            print(f"Found {len(concepts)} concepts matching '{args.concept}':")
            for concept in concepts:
                print(f"  - {concept['name']} (ID: {concept['id']})")

        # Get related concepts
        if args.related:
            related_concepts = querier.get_related_concepts(args.related)
            print(f"Found {len(related_concepts)} concepts related to '{args.related}':")
            for concept in related_concepts:
                print(f"  - {concept['name']} (ID: {concept['id']}, Weight: {concept['weight']})")

        # Get documents by concept
        if args.documents:
            documents = querier.get_documents_by_concept(args.documents)
            print(f"Found {len(documents)} documents related to concept '{args.documents}':")
            for document in documents:
                print(f"  - {document['title']} (ID: {document['id']})")

        # Run custom query
        if args.query:
            results = querier.run_custom_query(args.query)
            print(f"Query results ({len(results)} records):")
            print(json.dumps(results, indent=2))

    finally:
        # Close the Neo4j connection
        querier.close()

if __name__ == "__main__":
    main()
