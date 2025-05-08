# GraphRAG Agent Tools

This directory contains standalone command-line tools for interacting with the GraphRAG MPC server. These tools can be used by AI agents or directly by users to perform various operations on the GraphRAG system.

## Configuration

All tools use the following environment variables for configuration:

- `MPC_HOST`: MPC server host (default: localhost)
- `MPC_PORT`: MPC server port (default: 8766)
- `NEO4J_URI`: Neo4j database URI (default: bolt://localhost:7688)
- `NEO4J_USERNAME`: Neo4j username (default: neo4j)
- `NEO4J_PASSWORD`: Neo4j password (default: graphrag)

You can override these defaults by setting the environment variables or by using the `--url` parameter in each tool.

## Available Tools

### Utility Tools

- **ping.py**: Test if the MPC server is alive and responding
  ```
  python ping.py [--url URL]
  ```

### Search Tools

- **search.py**: Perform a hybrid search using both vector and graph databases
  ```
  python search.py --query QUERY [--n-results N] [--max-hops HOPS] [--url URL]
  ```

- **concept.py**: Get information about a specific concept
  ```
  python concept.py --name CONCEPT_NAME [--url URL]
  ```

- **documents.py**: List documents in the data store
  ```
  python documents.py [--limit LIMIT] [--url URL]
  ```

- **books-by-concept.py**: List books that cover a specific concept
  ```
  python books-by-concept.py --name CONCEPT_NAME [--limit LIMIT] [--url URL]
  ```

- **related-concepts.py**: List concepts related to a given concept
  ```
  python related-concepts.py --name CONCEPT_NAME [--limit LIMIT] [--url URL]
  ```

- **passages-about-concept.py**: Retrieve passages about a specific concept
  ```
  python passages-about-concept.py --name CONCEPT_NAME [--limit LIMIT] [--url URL]
  ```

### Document Addition Tools

- **add-document.py**: Add a document to the RAG system
  ```
  python add-document.py --text TEXT [--file FILE] [--metadata KEY=VALUE...] [--async] [--url URL]
  ```

- **add-folder.py**: Add a folder of documents (works asynchronously)
  ```
  python add-folder.py --path FOLDER_PATH [--recursive] [--file-types EXT1,EXT2,...] [--metadata KEY=VALUE...] [--sync] [--url URL]
  ```

### Job Management Tools

- **job-status.py**: Get information on a specific job
  ```
  python job-status.py --job-id JOB_ID [--url URL]
  ```

- **list-jobs.py**: List all jobs in the system
  ```
  python list-jobs.py [--status STATUS] [--type TYPE] [--url URL]
  ```

- **cancel-job.py**: Cancel a job
  ```
  python cancel-job.py --job-id JOB_ID [--url URL]
  ```

## Common Options

All tools support the following common options:

- `--url URL`: Override the MPC server URL (default: ws://localhost:8766 or from environment variables)
- `--raw`: Display the raw JSON response instead of formatted output

## Examples

### Search for information about neural networks

```bash
python search.py --query "How do neural networks work?"
```

### Get information about a concept

```bash
python concept.py --name "Machine Learning"
```

### Add a document from a file

```bash
python add-document.py --file /path/to/document.pdf --metadata title="My Document" author="John Doe"
```

### Add a folder of documents recursively

```bash
python add-folder.py --path /path/to/documents --recursive --file-types pdf,txt,md
```

### Check the status of a job

```bash
python job-status.py --job-id 12345678-1234-5678-1234-567812345678
```

### List all running jobs

```bash
python list-jobs.py --status running
```

### Cancel a job

```bash
python cancel-job.py --job-id 12345678-1234-5678-1234-567812345678
```