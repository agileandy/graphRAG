"""
Script to batch process multiple documents into the GraphRAG system.

This script demonstrates how to:
1. Process multiple documents from a directory
2. Extract entities and relationships
3. Add them to the GraphRAG system
"""
import sys
import os
import json
import argparse
from typing import List, Dict, Any
import glob

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.neo4j_db import Neo4jDatabase
from src.database.vector_db import VectorDatabase
from scripts.add_document import add_document_to_graphrag

def process_directory(directory_path: str, neo4j_db: Neo4jDatabase, vector_db: VectorDatabase) -> List[Dict[str, Any]]:
    """
    Process all text files in a directory.
    
    Args:
        directory_path: Path to directory containing text files
        neo4j_db: Neo4j database instance
        vector_db: Vector database instance
        
    Returns:
        List of processing results
    """
    # Find all text files in the directory
    text_files = glob.glob(os.path.join(directory_path, "*.txt"))
    json_files = glob.glob(os.path.join(directory_path, "*.json"))
    
    print(f"Found {len(text_files)} text files and {len(json_files)} JSON files")
    
    results = []
    
    # Process text files
    for file_path in text_files:
        file_name = os.path.basename(file_path)
        print(f"\nProcessing file: {file_name}")
        
        # Read the file
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        # Create metadata from filename
        metadata = {
            "title": os.path.splitext(file_name)[0],
            "source": "Text File",
            "file_path": file_path
        }
        
        # Add document to GraphRAG system
        result = add_document_to_graphrag(
            text=text,
            metadata=metadata,
            neo4j_db=neo4j_db,
            vector_db=vector_db
        )
        
        results.append(result)
    
    # Process JSON files (assuming they have a "text" field and other fields as metadata)
    for file_path in json_files:
        file_name = os.path.basename(file_path)
        print(f"\nProcessing file: {file_name}")
        
        # Read the file
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Extract text and metadata
        text = data.pop("text", "")
        if not text:
            print(f"Skipping {file_name}: No 'text' field found")
            continue
        
        # Use remaining fields as metadata
        metadata = data
        metadata["source"] = "JSON File"
        metadata["file_path"] = file_path
        
        # Add document to GraphRAG system
        result = add_document_to_graphrag(
            text=text,
            metadata=metadata,
            neo4j_db=neo4j_db,
            vector_db=vector_db
        )
        
        results.append(result)
    
    return results

def create_example_files(output_dir: str) -> None:
    """
    Create example files for testing.
    
    Args:
        output_dir: Directory to create example files in
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Example text files
    example_texts = [
        {
            "filename": "machine_learning_basics.txt",
            "content": """
            Machine Learning Basics
            
            Machine learning is a subset of artificial intelligence that provides systems the ability 
            to automatically learn and improve from experience without being explicitly programmed. 
            Machine learning focuses on the development of computer programs that can access data and 
            use it to learn for themselves.
            
            The process of learning begins with observations or data, such as examples, direct experience, 
            or instruction, in order to look for patterns in data and make better decisions in the future 
            based on the examples that we provide. The primary aim is to allow the computers to learn 
            automatically without human intervention or assistance and adjust actions accordingly.
            
            Supervised learning, unsupervised learning, and reinforcement learning are the three main 
            categories of machine learning algorithms. Supervised learning uses labeled training data to 
            learn the mapping function from the input variables to the output variable. Unsupervised 
            learning, on the other hand, does not have labeled outputs, so its goal is to infer the 
            natural structure present within a set of data points. Reinforcement learning is a type of 
            machine learning where an agent learns to behave in an environment by performing actions and 
            seeing the results.
            """
        },
        {
            "filename": "computer_vision.txt",
            "content": """
            Computer Vision: Enabling Machines to See
            
            Computer vision is a field of artificial intelligence that trains computers to interpret and 
            understand the visual world. Using digital images from cameras and videos and deep learning 
            models, machines can accurately identify and classify objects and then react to what they "see."
            
            Computer vision works in three basic steps: acquiring an image, processing the image, and 
            understanding the image. Image acquisition can be as simple as retrieving a digital image from 
            a database or as complex as producing 3D images from multiple angles. Image processing involves 
            methods like noise reduction, contrast enhancement, and image sharpening to bring out features 
            of interest. Image understanding is where machine learning and deep learning algorithms come into 
            play, allowing the system to recognize patterns and make decisions.
            
            Convolutional Neural Networks (CNNs) have revolutionized computer vision by automatically learning 
            hierarchical feature representations from raw image data. These networks consist of multiple layers, 
            including convolutional layers, pooling layers, and fully connected layers, each serving a specific 
            purpose in the feature extraction and classification process.
            
            Applications of computer vision are vast and growing, including facial recognition, autonomous 
            vehicles, medical image analysis, surveillance, augmented reality, and quality control in manufacturing.
            """
        },
        {
            "filename": "natural_language_processing.txt",
            "content": """
            Natural Language Processing: Bridging Humans and Machines
            
            Natural Language Processing (NLP) is a field of artificial intelligence that focuses on the interaction 
            between computers and humans through natural language. The ultimate objective of NLP is to read, 
            decipher, understand, and make sense of human language in a valuable way.
            
            NLP combines computational linguistics—rule-based modeling of human language—with statistical, machine 
            learning, and deep learning models. These technologies enable computers to process human language in the 
            form of text or voice data and to 'understand' its full meaning, complete with the speaker or writer's 
            intent and sentiment.
            
            The development of NLP applications is challenging because computers traditionally require humans to 
            communicate with them in a programming language that is precise, unambiguous, and highly structured. 
            Human speech, however, is not always precise; it is often ambiguous and the linguistic structure can 
            depend on many complex variables, including slang, regional dialects, and social context.
            
            Transformers have revolutionized NLP with their attention mechanism, which allows the model to focus on 
            different parts of the input sequence when producing the output. Models like BERT, GPT, and T5 have 
            achieved state-of-the-art results on a wide range of NLP tasks, including text classification, question 
            answering, and language translation.
            
            Applications of NLP include sentiment analysis, chatbots, language translation, speech recognition, 
            text summarization, and information extraction.
            """
        }
    ]
    
    # Example JSON files
    example_jsons = [
        {
            "filename": "reinforcement_learning.json",
            "content": {
                "title": "Reinforcement Learning: Learning from Interaction",
                "author": "AI Researcher",
                "category": "Machine Learning",
                "date": "2023-05-15",
                "text": """
                Reinforcement Learning (RL) is an area of machine learning concerned with how intelligent agents 
                ought to take actions in an environment in order to maximize the notion of cumulative reward. 
                Reinforcement learning is one of three basic machine learning paradigms, alongside supervised 
                learning and unsupervised learning.
                
                Reinforcement learning differs from supervised learning in that labeled input/output pairs need 
                not be presented, and sub-optimal actions need not be explicitly corrected. Instead the focus is 
                on finding a balance between exploration (of uncharted territory) and exploitation (of current 
                knowledge).
                
                The environment is typically stated in the form of a Markov decision process (MDP), because many 
                reinforcement learning algorithms for this context utilize dynamic programming techniques. The 
                main difference between the classical dynamic programming methods and reinforcement learning 
                algorithms is that the latter do not assume knowledge of an exact mathematical model of the MDP 
                and they target large MDPs where exact methods become infeasible.
                
                Deep reinforcement learning combines deep learning with reinforcement learning. Deep neural networks 
                are used to approximate the value function, policy, or model of the environment. This approach has 
                led to significant achievements, such as defeating world champions in the game of Go and mastering 
                complex video games.
                """
            }
        },
        {
            "filename": "generative_ai.json",
            "content": {
                "title": "Generative AI: Creating New Content",
                "author": "Tech Writer",
                "category": "Artificial Intelligence",
                "date": "2023-06-20",
                "text": """
                Generative AI refers to artificial intelligence systems that can generate new content, including 
                text, images, audio, and video, that resembles human-created content. These systems learn patterns 
                from existing data and use that knowledge to create new, original outputs.
                
                At the core of many generative AI systems are generative models such as Generative Adversarial 
                Networks (GANs), Variational Autoencoders (VAEs), and autoregressive models like the Transformer. 
                GANs consist of two neural networks—a generator and a discriminator—that are trained together in 
                a competitive process. The generator creates new data instances while the discriminator evaluates 
                them for authenticity.
                
                Large Language Models (LLMs) like GPT (Generative Pre-trained Transformer) have demonstrated 
                remarkable capabilities in generating coherent and contextually relevant text across a wide range 
                of topics and styles. These models are trained on vast amounts of text data and can perform various 
                tasks, including text completion, translation, summarization, and even code generation.
                
                Diffusion models have emerged as a powerful approach for image generation. These models start with 
                random noise and gradually transform it into a coherent image by learning to reverse a diffusion 
                process. Models like DALL-E, Midjourney, and Stable Diffusion can generate highly realistic images 
                from textual descriptions.
                
                Generative AI has numerous applications, including content creation, design assistance, data 
                augmentation for training other AI systems, and simulation for testing and development. However, 
                it also raises ethical concerns related to misinformation, copyright, and the potential misuse of 
                the technology.
                """
            }
        }
    ]
    
    # Write example text files
    for example in example_texts:
        file_path = os.path.join(output_dir, example["filename"])
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(example["content"])
        print(f"Created example text file: {file_path}")
    
    # Write example JSON files
    for example in example_jsons:
        file_path = os.path.join(output_dir, example["filename"])
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(example["content"], f, indent=2)
        print(f"Created example JSON file: {file_path}")

def main():
    """
    Main function to demonstrate batch processing of documents.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Batch process documents into the GraphRAG system")
    parser.add_argument("--dir", "-d", type=str, help="Directory containing documents to process")
    parser.add_argument("--create-examples", "-c", action="store_true", help="Create example files for testing")
    parser.add_argument("--example-dir", "-e", type=str, default="./example_docs", help="Directory for example files")
    args = parser.parse_args()
    
    # Create example files if requested
    if args.create_examples:
        create_example_files(args.example_dir)
        print(f"\nExample files created in {args.example_dir}")
        print(f"You can now run: python {__file__} --dir {args.example_dir}")
        return
    
    # Check if directory is provided
    if not args.dir:
        print("Please provide a directory containing documents to process")
        print(f"Example: python {__file__} --dir ./example_docs")
        print(f"Or create example files first: python {__file__} --create-examples")
        return
    
    # Check if directory exists
    if not os.path.isdir(args.dir):
        print(f"Directory not found: {args.dir}")
        return
    
    # Initialize databases
    neo4j_db = Neo4jDatabase()
    vector_db = VectorDatabase()
    
    # Verify connections
    if not neo4j_db.verify_connection():
        print("❌ Neo4j connection failed!")
        return
    
    if not vector_db.verify_connection():
        print("❌ Vector database connection failed!")
        return
    
    print("✅ Database connections verified!")
    
    # Process documents
    results = process_directory(args.dir, neo4j_db, vector_db)
    
    # Print summary
    print(f"\nProcessed {len(results)} documents")
    print(f"Added {sum(len(r['entities']) for r in results)} entities to Neo4j")
    print(f"Added {sum(len(r['relationships']) for r in results)} relationships to Neo4j")
    
    # Close Neo4j connection
    neo4j_db.close()

if __name__ == "__main__":
    main()