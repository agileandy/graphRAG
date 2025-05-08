"""
Script to visualize the Neo4j knowledge graph.

This script:
1. Exports graph data from Neo4j
2. Creates interactive visualizations using Pyvis
3. Saves the visualizations as HTML files
"""
import sys
import os
import argparse
import json

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.neo4j_db import Neo4jDatabase

try:
    from pyvis.network import Network
    PYVIS_AVAILABLE = True
except ImportError:
    PYVIS_AVAILABLE = False

def install_pyvis():
    """
    Install the pyvis library if not already installed.
    """
    import subprocess
    print("Installing pyvis library...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyvis"])
    print("✅ Pyvis installed successfully!")
    print("Please restart the script to use pyvis.")
    sys.exit(0)

def visualize_concepts(neo4j_db: Neo4jDatabase, limit: int = 50, output_file: str = "concepts_graph.html") -> None:
    """
    Visualize concepts and their relationships.
    
    Args:
        neo4j_db: Neo4j database instance
        limit: Maximum number of nodes to include
        output_file: Output HTML file
    """
    print(f"Creating visualization of concepts (limit: {limit})...")
    
    # Get concepts and relationships
    query = f"""
    MATCH (c1:Concept)-[r:RELATED_TO]-(c2:Concept)
    RETURN c1.id AS source_id, c1.name AS source_name, 
           c2.id AS target_id, c2.name AS target_name,
           r.strength AS strength
    LIMIT {limit}
    """
    relationships = neo4j_db.run_query(query)
    
    # Create network
    net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white")
    
    # Add nodes and edges
    added_nodes = set()
    
    for rel in relationships:
        source_id = rel["source_id"]
        target_id = rel["target_id"]
        source_name = rel["source_name"]
        target_name = rel["target_name"]
        strength = rel.get("strength", 0.5)
        
        # Add source node if not already added
        if source_id not in added_nodes:
            net.add_node(source_id, label=source_name, title=source_name, size=20)
            added_nodes.add(source_id)
        
        # Add target node if not already added
        if target_id not in added_nodes:
            net.add_node(target_id, label=target_name, title=target_name, size=20)
            added_nodes.add(target_id)
        
        # Add edge
        net.add_edge(source_id, target_id, value=strength*5, title=f"Strength: {strength}")
    
    # Set physics layout
    net.barnes_hut(gravity=-80000, central_gravity=0.3, spring_length=250, spring_strength=0.001, damping=0.09)
    
    # Save visualization
    net.save_graph(output_file)
    print(f"✅ Visualization saved to {output_file}")
    
    # Open in browser
    print("Opening visualization in browser...")
    import webbrowser
    webbrowser.open(f"file://{os.path.abspath(output_file)}")

def visualize_book_concepts(neo4j_db: Neo4jDatabase, book_title: str = None, output_file: str = "book_concepts_graph.html") -> None:
    """
    Visualize books and their related concepts.
    
    Args:
        neo4j_db: Neo4j database instance
        book_title: Title of the book to visualize (if None, visualize all books)
        output_file: Output HTML file
    """
    if book_title:
        print(f"Creating visualization of concepts for book: {book_title}...")
        
        # Find the book by title
        query = """
        MATCH (b:Book)
        WHERE b.title CONTAINS $title
        RETURN b.id AS id, b.title AS title
        """
        books = neo4j_db.run_query(query, {"title": book_title})
        
        if not books:
            print(f"No book found with title containing '{book_title}'")
            return
        
        # Use the first matching book
        book_id = books[0]["id"]
        book_title = books[0]["title"]
        
        # Get concepts related to this book
        query = """
        MATCH (b:Book {id: $book_id})-[:MENTIONS]->(c:Concept)
        OPTIONAL MATCH (c)-[r:RELATED_TO]-(c2:Concept)<-[:MENTIONS]-(b)
        RETURN b.id AS book_id, b.title AS book_title,
               c.id AS concept_id, c.name AS concept_name,
               c2.id AS related_id, c2.name AS related_name,
               r.strength AS strength
        """
        results = neo4j_db.run_query(query, {"book_id": book_id})
    else:
        print("Creating visualization of all books and their concepts...")
        
        # Get all books and their concepts
        query = """
        MATCH (b:Book)-[:MENTIONS]->(c:Concept)
        RETURN b.id AS book_id, b.title AS book_title,
               c.id AS concept_id, c.name AS concept_name
        """
        results = neo4j_db.run_query(query)
    
    # Create network
    net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white")
    
    # Add nodes and edges
    added_nodes = set()
    
    # Add book nodes
    book_nodes = {}
    concept_nodes = {}
    
    for result in results:
        book_id = result["book_id"]
        book_title = result["book_title"]
        concept_id = result["concept_id"]
        concept_name = result["concept_name"]
        
        # Add book node if not already added
        if book_id not in added_nodes:
            net.add_node(book_id, label=book_title, title=book_title, color="#ff9999", size=30)
            added_nodes.add(book_id)
            book_nodes[book_id] = book_title
        
        # Add concept node if not already added
        if concept_id not in added_nodes:
            net.add_node(concept_id, label=concept_name, title=concept_name, color="#99ccff", size=20)
            added_nodes.add(concept_id)
            concept_nodes[concept_id] = concept_name
        
        # Add edge from book to concept
        net.add_edge(book_id, concept_id, color="#ffffff")
        
        # Add edges between related concepts
        if "related_id" in result and result["related_id"]:
            related_id = result["related_id"]
            related_name = result["related_name"]
            strength = result.get("strength", 0.5)
            
            # Add related concept node if not already added
            if related_id not in added_nodes:
                net.add_node(related_id, label=related_name, title=related_name, color="#99ccff", size=20)
                added_nodes.add(related_id)
                concept_nodes[related_id] = related_name
            
            # Add edge between concepts
            net.add_edge(concept_id, related_id, value=strength*3, title=f"Strength: {strength}", color="#ffcc99")
    
    # Set physics layout
    net.barnes_hut(gravity=-80000, central_gravity=0.3, spring_length=250, spring_strength=0.001, damping=0.09)
    
    # Save visualization
    net.save_graph(output_file)
    print(f"✅ Visualization saved to {output_file}")
    
    # Open in browser
    print("Opening visualization in browser...")
    import webbrowser
    webbrowser.open(f"file://{os.path.abspath(output_file)}")

def visualize_concept_neighborhood(neo4j_db: Neo4jDatabase, concept_name: str, max_hops: int = 2, output_file: str = "concept_neighborhood.html") -> None:
    """
    Visualize a concept and its neighborhood.
    
    Args:
        neo4j_db: Neo4j database instance
        concept_name: Name of the concept to visualize
        max_hops: Maximum number of hops in the graph
        output_file: Output HTML file
    """
    print(f"Creating visualization of concept neighborhood: {concept_name} (max hops: {max_hops})...")
    
    # Find the concept by name
    query = """
    MATCH (c:Concept)
    WHERE toLower(c.name) CONTAINS toLower($name)
    RETURN c.id AS id, c.name AS name
    """
    concepts = neo4j_db.run_query(query, {"name": concept_name})
    
    if not concepts:
        print(f"No concept found with name containing '{concept_name}'")
        return
    
    # Use the first matching concept
    concept_id = concepts[0]["id"]
    concept_name = concepts[0]["name"]
    
    # Get neighborhood
    query = f"""
    MATCH path = (c:Concept {{id: $concept_id}})-[r:RELATED_TO*1..{max_hops}]-(related:Concept)
    RETURN c.id AS source_id, c.name AS source_name,
           related.id AS target_id, related.name AS target_name,
           length(path) - 1 AS distance
    """
    results = neo4j_db.run_query(query, {"concept_id": concept_id})
    
    # Create network
    net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white")
    
    # Add central concept node
    net.add_node(concept_id, label=concept_name, title=concept_name, color="#ff9999", size=30)
    added_nodes = {concept_id}
    
    # Add related concept nodes and edges
    for result in results:
        target_id = result["target_id"]
        target_name = result["target_name"]
        distance = result["distance"]
        
        # Calculate color based on distance
        if distance == 1:
            color = "#99ccff"  # Direct connections
        elif distance == 2:
            color = "#99ffcc"  # 2-hop connections
        else:
            color = "#cccccc"  # Further connections
        
        # Add target node if not already added
        if target_id not in added_nodes:
            net.add_node(target_id, label=target_name, title=target_name, color=color, size=20)
            added_nodes.add(target_id)
        
        # Add edge
        net.add_edge(concept_id, target_id, title=f"Distance: {distance}")
    
    # Set physics layout
    net.barnes_hut(gravity=-80000, central_gravity=0.3, spring_length=250, spring_strength=0.001, damping=0.09)
    
    # Save visualization
    net.save_graph(output_file)
    print(f"✅ Visualization saved to {output_file}")
    
    # Open in browser
    print("Opening visualization in browser...")
    import webbrowser
    webbrowser.open(f"file://{os.path.abspath(output_file)}")

def export_graph_data(neo4j_db: Neo4jDatabase, output_file: str = "graph_data.json") -> None:
    """
    Export graph data to a JSON file.
    
    Args:
        neo4j_db: Neo4j database instance
        output_file: Output JSON file
    """
    print(f"Exporting graph data to {output_file}...")
    
    # Get all books
    query = """
    MATCH (b:Book)
    RETURN b.id AS id, b.title AS title, b.filename AS filename
    """
    books = neo4j_db.run_query(query)
    
    # Get all concepts
    query = """
    MATCH (c:Concept)
    RETURN c.id AS id, c.name AS name, c.abbreviation AS abbreviation
    """
    concepts = neo4j_db.run_query(query)
    
    # Get all book-concept relationships
    query = """
    MATCH (b:Book)-[:MENTIONS]->(c:Concept)
    RETURN b.id AS book_id, c.id AS concept_id
    """
    book_concept_rels = neo4j_db.run_query(query)
    
    # Get all concept-concept relationships
    query = """
    MATCH (c1:Concept)-[r:RELATED_TO]->(c2:Concept)
    RETURN c1.id AS source_id, c2.id AS target_id, r.strength AS strength
    """
    concept_rels = neo4j_db.run_query(query)
    
    # Create graph data
    graph_data = {
        "books": books,
        "concepts": concepts,
        "book_concept_relationships": book_concept_rels,
        "concept_relationships": concept_rels
    }
    
    # Save to JSON file
    with open(output_file, "w") as f:
        json.dump(graph_data, f, indent=2)
    
    print(f"✅ Graph data exported to {output_file}")
    print("Summary:")
    print(f"  Books: {len(books)}")
    print(f"  Concepts: {len(concepts)}")
    print(f"  Book-Concept Relationships: {len(book_concept_rels)}")
    print(f"  Concept-Concept Relationships: {len(concept_rels)}")

def main():
    """
    Main function to visualize the Neo4j knowledge graph.
    """
    # Check if pyvis is installed
    if not PYVIS_AVAILABLE:
        install_pyvis()
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Visualize the Neo4j knowledge graph")
    parser.add_argument("--concepts", action="store_true", help="Visualize concepts and their relationships")
    parser.add_argument("--books", action="store_true", help="Visualize books and their concepts")
    parser.add_argument("--book", type=str, help="Visualize a specific book and its concepts")
    parser.add_argument("--concept", type=str, help="Visualize a concept and its neighborhood")
    parser.add_argument("--export", action="store_true", help="Export graph data to a JSON file")
    parser.add_argument("--limit", type=int, default=50, help="Maximum number of nodes to include")
    parser.add_argument("--hops", type=int, default=2, help="Maximum number of hops in the graph")
    parser.add_argument("--output", type=str, help="Output file")
    args = parser.parse_args()
    
    # Initialize Neo4j database
    neo4j_db = Neo4jDatabase()
    
    # Verify connection
    if not neo4j_db.verify_connection():
        print("❌ Neo4j connection failed!")
        return
    
    print("✅ Neo4j connection verified!")
    
    # Perform the requested operation
    if args.concepts:
        output_file = args.output or "concepts_graph.html"
        visualize_concepts(neo4j_db, args.limit, output_file)
    elif args.book:
        output_file = args.output or "book_concepts_graph.html"
        visualize_book_concepts(neo4j_db, args.book, output_file)
    elif args.books:
        output_file = args.output or "all_books_graph.html"
        visualize_book_concepts(neo4j_db, None, output_file)
    elif args.concept:
        output_file = args.output or "concept_neighborhood.html"
        visualize_concept_neighborhood(neo4j_db, args.concept, args.hops, output_file)
    elif args.export:
        output_file = args.output or "graph_data.json"
        export_graph_data(neo4j_db, output_file)
    else:
        # If no arguments provided, run an interactive demo
        while True:
            print("\nGraph Visualization Options")
            print("="*50)
            print("1. Visualize concepts and their relationships")
            print("2. Visualize all books and their concepts")
            print("3. Visualize a specific book and its concepts")
            print("4. Visualize a concept and its neighborhood")
            print("5. Export graph data to a JSON file")
            print("6. Exit")
            
            choice = input("\nEnter your choice (1-6): ")
            
            if choice == "1":
                limit = int(input("Maximum number of nodes (default: 50): ") or "50")
                output_file = input("Output file (default: concepts_graph.html): ") or "concepts_graph.html"
                visualize_concepts(neo4j_db, limit, output_file)
            elif choice == "2":
                output_file = input("Output file (default: all_books_graph.html): ") or "all_books_graph.html"
                visualize_book_concepts(neo4j_db, None, output_file)
            elif choice == "3":
                book_title = input("Enter book title: ")
                output_file = input("Output file (default: book_concepts_graph.html): ") or "book_concepts_graph.html"
                visualize_book_concepts(neo4j_db, book_title, output_file)
            elif choice == "4":
                concept_name = input("Enter concept name: ")
                hops = int(input("Maximum hops (default: 2): ") or "2")
                output_file = input("Output file (default: concept_neighborhood.html): ") or "concept_neighborhood.html"
                visualize_concept_neighborhood(neo4j_db, concept_name, hops, output_file)
            elif choice == "5":
                output_file = input("Output file (default: graph_data.json): ") or "graph_data.json"
                export_graph_data(neo4j_db, output_file)
            elif choice == "6":
                break
            else:
                print("Invalid choice. Please try again.")
    
    # Close Neo4j connection
    neo4j_db.close()

if __name__ == "__main__":
    main()