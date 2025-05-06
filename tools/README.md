# GraphRAG Tools

This directory contains tools for interacting with the GraphRAG system.

## GraphRAG MPC Client

The GraphRAG MPC client is a command-line tool for interacting with the GraphRAG MPC server. It provides a simple interface for adding documents, searching for documents, and getting information about concepts.

### Installation

The tool is already installed in the GraphRAG Docker container. If you want to use it outside the container, you need to install the required dependencies:

```bash
pip install websockets
```

### Usage

```bash
./graphrag <command> [options]
```

or

```bash
python graphrag_mpc_client.py <command> [options]
```

### Commands

#### Add Document

Add a document to the GraphRAG system:

```bash
./graphrag add-document --text "Document text" --metadata "title=Title,author=Author,category=Category,concepts=Concept1,Concept2"
```

You can also read the document text from a file:

```bash
./graphrag add-document --file /path/to/document.txt --metadata "title=Title,author=Author,category=Category,concepts=Concept1,Concept2"
```

#### Add Folder

Add all documents in a folder to the GraphRAG system:

```bash
./graphrag add-folder --path /path/to/folder --metadata "category=Category,concepts=Concept1,Concept2"
```

#### Search

Search for documents in the GraphRAG system:

```bash
./graphrag search --query "Search query" --limit 10
```

#### Get Concept

Get information about a concept:

```bash
./graphrag concept --name "Concept name"
```

#### Get Related Concepts

Get concepts related to a given concept:

```bash
./graphrag related-concepts --name "Concept name"
```

#### Get Passages About Concept

Get passages that mention a given concept:

```bash
./graphrag passages-about-concept --name "Concept name"
```

#### Get Books By Concept

Get books that mention a given concept:

```bash
./graphrag books-by-concept --name "Concept name"
```

#### Get Documents

Get a list of documents in the GraphRAG system:

```bash
./graphrag documents --limit 10
```

### Examples

#### Add a Document

```bash
./graphrag add-document --text "GraphRAG is a hybrid approach that combines vector embeddings with knowledge graphs for enhanced information retrieval." --metadata "title=Introduction to GraphRAG,author=Test User,category=AI,concepts=GraphRAG,RAG,Knowledge Graph,Vector Embeddings"
```

#### Search for Documents

```bash
./graphrag search --query "GraphRAG"
```

#### Get Information About a Concept

```bash
./graphrag concept --name "GraphRAG"
```

#### Get Related Concepts

```bash
./graphrag related-concepts --name "GraphRAG"
```

#### Get Passages About a Concept

```bash
./graphrag passages-about-concept --name "GraphRAG"
```

### Configuration

By default, the tool connects to the MPC server at `ws://localhost:8766`. You can specify a different URL using the `--url` option:

```bash
./graphrag --url ws://example.com:8765 search --query "GraphRAG"
```

### Exit Codes

The tool returns the following exit codes:

- `0`: Success
- `1`: Error (connection error, invalid command, etc.)
