"""
Neo4j database connection and operations for GraphRAG project.
"""
import os
from typing import Dict, List, Optional, Any, Union
from dotenv import load_dotenv
from neo4j import GraphDatabase, Driver, Session, Result

# Load environment variables
load_dotenv()

class Neo4jDatabase:
    """
    Neo4j database connection and operations for GraphRAG project.
    """
    def __init__(self, uri: Optional[str] = None, username: Optional[str] = None, 
                 password: Optional[str] = None):
        """
        Initialize Neo4j database connection.
        
        Args:
            uri: Neo4j URI (default: from environment variable)
            username: Neo4j username (default: from environment variable)
            password: Neo4j password (default: from environment variable)
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = username or os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "graphrag")
        self.driver: Optional[Driver] = None
        
    def connect(self) -> None:
        """
        Connect to Neo4j database.
        """
        if self.driver is None:
            self.driver = GraphDatabase.driver(
                self.uri, auth=(self.username, self.password)
            )
            
    def close(self) -> None:
        """
        Close Neo4j database connection.
        """
        if self.driver is not None:
            self.driver.close()
            self.driver = None
            
    def verify_connection(self) -> bool:
        """
        Verify Neo4j database connection.
        
        Returns:
            True if connection is successful, False otherwise.
        """
        try:
            self.connect()
            with self.driver.session() as session:
                result = session.run("RETURN 1 AS result")
                return result.single()["result"] == 1
        except Exception as e:
            print(f"Neo4j connection error: {e}")
            return False
        
    def run_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Run a Cypher query and return all records as a list of dictionaries.
        
        Args:
            query: Cypher query
            parameters: Query parameters
            
        Returns:
            List of records as dictionaries
        """
        self.connect()
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            # Convert all records to dictionaries
            return [dict(record) for record in result]
            
    def run_query_and_return_single(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run a Cypher query and return a single record.
        
        Args:
            query: Cypher query
            parameters: Query parameters
            
        Returns:
            Single record as dictionary
        """
        self.connect()
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            record = result.single()
            if record:
                return dict(record)
            return {}
            
    def create_schema(self) -> None:
        """
        Create initial Neo4j schema with constraints and indexes.
        """
        # Create constraints for unique identifiers
        constraints = [
            "CREATE CONSTRAINT book_id IF NOT EXISTS FOR (b:Book) REQUIRE b.id IS UNIQUE",
            "CREATE CONSTRAINT chapter_id IF NOT EXISTS FOR (c:Chapter) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT section_id IF NOT EXISTS FOR (s:Section) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT concept_id IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE"
        ]
        
        # Create indexes for common properties
        indexes = [
            "CREATE INDEX book_title IF NOT EXISTS FOR (b:Book) ON (b.title)",
            "CREATE INDEX concept_name IF NOT EXISTS FOR (c:Concept) ON (c.name)"
        ]
        
        self.connect()
        with self.driver.session() as session:
            for constraint in constraints:
                session.run(constraint)
            for index in indexes:
                session.run(index)
                
    def clear_database(self) -> None:
        """
        Clear all data from the database.
        WARNING: This will delete all nodes and relationships.
        """
        self.connect()
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            
    def create_dummy_data(self) -> None:
        """
        Create dummy data for testing.
        """
        # Create some books
        books_query = """
        CREATE (b1:Book {id: 'book-001', title: 'Introduction to Machine Learning', 
                         category: 'AI', isbn: '978-1-234567-89-0'})
        CREATE (b2:Book {id: 'book-002', title: 'Deep Learning Fundamentals', 
                         category: 'AI', isbn: '978-1-234567-89-1'})
                         
        // Create chapters for book 1
        CREATE (c1:Chapter {id: 'chapter-001', title: 'Supervised Learning', 
                           number: 1, book_id: 'book-001'})
        CREATE (c2:Chapter {id: 'chapter-002', title: 'Unsupervised Learning', 
                           number: 2, book_id: 'book-001'})
                           
        // Create sections for chapter 1
        CREATE (s1:Section {id: 'section-001', title: 'Classification', 
                           number: 1, chapter_id: 'chapter-001'})
        CREATE (s2:Section {id: 'section-002', title: 'Regression', 
                           number: 2, chapter_id: 'chapter-001'})
                           
        // Create concepts
        CREATE (concept1:Concept {id: 'concept-001', name: 'Neural Networks'})
        CREATE (concept2:Concept {id: 'concept-002', name: 'Decision Trees'})
        CREATE (concept3:Concept {id: 'concept-003', name: 'Gradient Descent'})
        
        // Create relationships
        CREATE (b1)-[:CONTAINS]->(c1)
        CREATE (b1)-[:CONTAINS]->(c2)
        CREATE (c1)-[:CONTAINS]->(s1)
        CREATE (c1)-[:CONTAINS]->(s2)
        CREATE (s1)-[:MENTIONS]->(concept1)
        CREATE (s1)-[:MENTIONS]->(concept2)
        CREATE (s2)-[:MENTIONS]->(concept3)
        CREATE (concept1)-[:RELATED_TO {strength: 0.8}]->(concept3)
        CREATE (concept2)-[:RELATED_TO {strength: 0.6}]->(concept1)
        """
        
        self.connect()
        with self.driver.session() as session:
            session.run(books_query)