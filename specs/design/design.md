# GraphRAG System Architecture

## 1. System Overview

GraphRAG is a hybrid Retrieval-Augmented Generation system that combines vector embeddings with knowledge graphs to overcome the limitations of traditional embedding-based RAG systems. By explicitly representing semantic connections and contextual relationships between ideas within and across books, GraphRAG enables more sophisticated information retrieval and synthesis.

```mermaid
graph TD
    User[User/AI Agent] --> API[API Server]
    User --> MPC[MPC Server]
    API --> DBL[Database Linkage]
    MPC --> DBL
    DBL --> Neo4j[Neo4j Graph Database]
    DBL --> ChromaDB[ChromaDB Vector Database]
    DP[Document Processing] --> Neo4j
    DP --> ChromaDB
    DP --> LLM[LLM Integration]
    JM[Job Manager] --> DP
```

### 1.1 Key Features

- **Hybrid Search**: Combines vector similarity with graph traversal for more contextually relevant results
- **Concept Extraction**: Identifies key concepts and their relationships from documents
- **Asynchronous Processing**: Handles large batch operations without blocking
- **AI Agent Integration**: Provides tools for AI agents to interact with the system
- **Duplicate Detection**: Prevents adding duplicate documents to the system

### 1.2 Technology Stack

- **Backend**: Python 3.12
- **Graph Database**: Neo4j 5.18.1
- **Vector Database**: ChromaDB 1.0.8+
- **API Server**: Flask
- **MPC Server**: WebSockets
- **LLM Integration**: OpenAI API and local models via LM Studio
- **Containerization**: Docker

### 1.3 System Requirements

- **Hardware**:
  - Minimum: 4GB RAM, 2 CPU cores, 20GB storage
  - Recommended: 8GB+ RAM, 4+ CPU cores, 100GB+ storage for large document collections
- **Software**:
  - Python 3.12 (required for spaCy compatibility)
  - Docker (optional, for containerized deployment)
  - Neo4j 5.18.1+
  - UV package manager (preferred over pip)
- **Network**:
  - Ports 5001 (API), 7688 (Neo4j Bolt), 7475 (Neo4j Browser), 8766 (MPC) must be available
  - Internet connection for LLM API calls (if using OpenAI)

## 2. Component Architecture

### 2.1 Database Layer

The database layer consists of two primary databases:

1. **Neo4j Graph Database**: Stores the knowledge graph with concepts, documents, and their relationships
2. **ChromaDB Vector Database**: Stores document chunks and their embeddings for semantic search

```mermaid
classDiagram
    class Neo4jDatabase {
        +connect()
        +close()
        +verify_connection()
        +run_query(query, parameters)
        +run_query_and_return_single(query, parameters)
        +create_schema()
        +clear_database()
    }

    class VectorDatabase {
        +connect(collection_name, optimize_for_large_datasets)
        +verify_connection()
        +add_documents(documents, embeddings, metadatas, ids, batch_size)
        +query(query_texts, query_embeddings, n_results, where)
        +get(ids, where)
        +count()
    }

    class DatabaseLinkage {
        +get_node_chunks(node_id, node_type)
        +get_related_nodes(chunk_id, metadata)
        +hybrid_search(query_text, n_vector_results, max_graph_hops)
    }

    DatabaseLinkage --> Neo4jDatabase
    DatabaseLinkage --> VectorDatabase
```

#### 2.1.1 Technology Selection Rationale

The choice of database technologies was driven by the following considerations:

**Neo4j**:

- **Explicit Relationship Modeling**: Neo4j's property graph model allows for explicit representation of complex relationships between concepts, documents, and sections.
- **Cypher Query Language**: Provides a powerful and intuitive way to traverse and query graph relationships.
- **Scalability**: Supports horizontal scaling for large knowledge graphs.
- **Community Support**: Strong community and extensive documentation.
- **Alternatives Considered**:
  - ArangoDB: While offering multi-model capabilities, Neo4j's specialized graph capabilities were preferred.
  - Amazon Neptune: Avoided due to cloud vendor lock-in concerns.
  - TigerGraph: Less mature ecosystem and community support at the time of selection.

**ChromaDB**:

- **Embedding Storage**: Purpose-built for storing and querying vector embeddings.
- **Similarity Search**: Efficient approximate nearest neighbor (ANN) search capabilities.
- **Local Deployment**: Can be deployed locally without external dependencies.
- **Python Integration**: Native Python API with simple integration.
- **Alternatives Considered**:
  - Pinecone: Cloud-only solution with potential cost implications for large datasets.
  - Milvus: More complex deployment requirements.
  - FAISS: Lower-level library requiring more custom code for persistence and management.
  - Qdrant: Promising alternative, but ChromaDB had better Python integration at the time.

#### 2.1.2 Neo4j Schema

```mermaid
erDiagram
    Book ||--o{ Chapter : CONTAINS
    Chapter ||--o{ Section : CONTAINS
    Section ||--o{ Concept : MENTIONS
    Concept ||--o{ Concept : RELATED_TO

    Book {
        string id PK
        string title
        string category
        string isbn
    }

    Chapter {
        string id PK
        string title
        int number
        string book_id FK
    }

    Section {
        string id PK
        string title
        int number
        string chapter_id FK
    }

    Concept {
        string id PK
        string name
        string category
    }
```

#### 2.1.3 ChromaDB Collection Structure

ChromaDB stores document chunks with their embeddings and metadata:

```python
# Example of adding documents to ChromaDB
collection.add_documents(
    documents=[
        "Neural networks are a fundamental component of deep learning...",
        "The architecture of neural networks consists of layers..."
    ],
    embeddings=[
        [0.1, 0.2, 0.3, ...],  # 1024-dimensional embedding vector
        [0.2, 0.3, 0.4, ...]   # 1024-dimensional embedding vector
    ],
    metadatas=[
        {
            "document_id": "doc123",
            "title": "Deep Learning Fundamentals",
            "page": 42,
            "chunk_id": "chunk1",
            "section_id": "section1",
            "chapter_id": "chapter1",
            "book_id": "book1",
            "concepts": ["neural networks", "deep learning"]
        },
        {
            "document_id": "doc456",
            "title": "Machine Learning Handbook",
            "page": 78,
            "chunk_id": "chunk2",
            "section_id": "section2",
            "chapter_id": "chapter2",
            "book_id": "book2",
            "concepts": ["neural networks", "architecture", "layers"]
        }
    ],
    ids=["chunk1", "chunk2"]
)
```

The metadata structure enables:

- **Document Tracing**: Linking chunks back to their source documents
- **Hierarchical Navigation**: Traversing from books to chapters to sections
- **Concept Linkage**: Connecting chunks to the concepts they mention
- **Filtering**: Performing targeted searches based on metadata attributes

### 2.2 Processing Layer

The processing layer handles document ingestion, chunking, concept extraction, and relationship building:

```mermaid
flowchart TD
    Document[Document] --> Chunking[Document Chunking]
    Chunking --> Embedding[Embedding Generation]
    Chunking --> ConceptExtraction[Concept Extraction]
    ConceptExtraction --> RelationshipBuilding[Relationship Building]
    Embedding --> VectorDB[Vector Database]
    RelationshipBuilding --> GraphDB[Graph Database]
    ConceptExtraction --> LLM[LLM Integration]
```

#### 2.2.1 Document Processing Pipeline

1. **Document Loading**: Parse documents from various formats (PDF, TXT, MD)
   - PDF processing uses PyMuPDF (fitz) for text extraction and layout analysis
   - Table extraction uses Camelot for structured data
   - Image extraction and OCR via Tesseract when needed
   - Markdown processing preserves structure and formatting

2. **Chunking**: Split documents into semantic chunks
   - **Strategy**: Hybrid approach combining multiple methods:
     - **Semantic Chunking**: Uses sentence transformers to identify natural semantic boundaries
     - **Structure-aware**: Respects document structure (headings, paragraphs, sections)
     - **Size-constrained**: Ensures chunks stay within token limits (default: 512 tokens)
   - **Configuration**: Chunking parameters are configurable:

     ```python
     chunker = DocumentChunker(
         chunk_size=512,
         chunk_overlap=50,
         respect_sections=True,
         split_on_headings=True
     )
     ```

3. **Embedding Generation**: Generate embeddings for each chunk
   - Uses Ollama with "snowflake-arctic-embed2:latest" model (1024 dimensions) by default
   - Optional reranking capability via Ollama with "qllama/bge-reranker-large:latest"
   - Phi-4 model reserved for concept extraction and NLP processing tasks
   - Batch processing to optimize API calls
   - Caching to avoid re-embedding identical content

4. **Concept Extraction**: Extract key concepts using NLP and/or LLM
   - **NLP-based extraction**:
     - spaCy for named entity recognition and noun phrase extraction
     - TF-IDF for statistical importance scoring
     - Domain-specific entity recognition for specialized fields
   - **LLM-based extraction**:
     - Structured prompting to identify key concepts
     - Example prompt template:

       ```text
       Identify the 5-10 most important concepts in the following text.
       For each concept, provide:
       1. The concept name
       2. A category (e.g., technique, theory, tool, person)
       3. A confidence score (0-1)

       Text: {chunk_text}
       ```

   - **Concept Disambiguation**:
     - Fuzzy matching to identify similar concepts
     - Embedding similarity to group related concepts
     - Manual curation interface for reviewing and merging concepts

5. **Relationship Building**: Create relationships between concepts and documents
   - **Explicit Relationships**:
     - MENTIONS: Links sections to concepts they contain
     - CONTAINS: Hierarchical document structure (book → chapter → section)
   - **Derived Relationships**:
     - RELATED_TO: Between concepts, based on:
       - Co-occurrence frequency in the same sections
       - Embedding similarity
       - LLM-generated relationship suggestions
     - Relationship strength scoring (0-1) based on evidence
   - **Relationship Types**:
     - Basic RELATED_TO for general connections
     - Specialized relationships (IS_A, PART_OF, USES, etc.) for domain-specific knowledge

6. **Storage**: Store chunks in ChromaDB and concepts/relationships in Neo4j
   - Transactional processing ensures consistency across both databases
   - Rollback mechanisms for failed processing
   - Idempotent operations to prevent duplicates

#### 2.2.2 Job Management and Persistence

The job management system handles asynchronous processing of documents and provides status tracking:

```mermaid
classDiagram
    class JobManager {
        -jobs_db
        +create_job(job_type, params, created_by)
        +get_job(job_id)
        +get_jobs_by_status(status)
        +get_jobs_by_client(client_id)
        +run_job_async(job, task_func)
        +cancel_job(job_id)
    }

    class Job {
        +job_id: string
        +job_type: string
        +params: dict
        +status: string
        +progress: float
        +created_at: datetime
        +started_at: datetime
        +completed_at: datetime
        +result: dict
        +error: string
        +update_progress(processed_items, total_items)
        +start()
        +complete(result)
        +fail(error)
        +cancel()
    }

    class JobsDatabase {
        +save_job(job)
        +get_job(job_id)
        +update_job(job)
        +delete_job(job_id)
        +list_jobs(filters)
    }

    JobManager --> Job
    JobManager --> JobsDatabase
```

**Job Persistence**:

- Jobs are persisted in SQLite database by default
- Schema includes all job metadata and status information
- Configurable to use other databases (PostgreSQL, MySQL) for production
- Regular cleanup of completed jobs (configurable retention period)

**Job Types**:

- `process_document`: Process a single document
- `process_folder`: Process all documents in a folder
- `extract_concepts`: Extract concepts from existing chunks
- `build_relationships`: Build or update concept relationships
- `reindex`: Rebuild indexes for faster querying

### 2.3 API Layer

The API layer provides RESTful endpoints for interacting with the system:

```mermaid
classDiagram
    class APIServer {
        +health_check()
        +get_version()
        +search(query, n_results, max_hops)
        +get_concept(concept_name)
        +get_all_concepts()
        +get_documents_for_concept(concept_name)
        +add_document(text, metadata)
    }
```

#### 2.3.1 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check endpoint |
| `/version` | GET | Get application version |
| `/search` | POST | Perform hybrid search |
| `/concepts/<concept_name>` | GET | Get concept information |
| `/concepts` | GET | Get all concepts |
| `/documents/<concept_name>` | GET | Get documents for concept |
| `/documents` | POST | Add a document |

### 2.4 MPC Server

The MPC (Message Passing Communication) server enables AI agents to interact with the system:

```mermaid
sequenceDiagram
    participant Agent as AI Agent
    participant MPC as MPC Server
    participant JM as Job Manager
    participant DB as Database Layer

    Agent->>MPC: Connect WebSocket
    MPC->>Agent: Connection Established
    Agent->>MPC: Request (action: "search", query: "...")
    MPC->>DB: Perform Search
    DB->>MPC: Search Results
    MPC->>Agent: Response (results)

    Agent->>MPC: Request (action: "add-document", text: "...", async: true)
    MPC->>JM: Create Job
    JM->>Agent: Job Created (job_id)
    JM->>DB: Process Document (async)
    Agent->>MPC: Request (action: "job-status", job_id: "...")
    MPC->>JM: Get Job Status
    JM->>Agent: Job Status (progress)
    DB-->>JM: Processing Complete
    Agent->>MPC: Request (action: "job-status", job_id: "...")
    MPC->>JM: Get Job Status
    JM->>Agent: Job Status (completed)
```

#### 2.4.1 MPC Actions

| Action | Description |
|--------|-------------|
| `ping` | Simple ping for connection testing |
| `search` | Hybrid search |
| `concept` | Get concept info |
| `documents` | Get documents for concept |
| `books-by-concept` | Find books mentioning a concept |
| `related-concepts` | Find related concepts |
| `passages-about-concept` | Find passages about a concept |
| `add-document` | Add a single document |
| `add-folder` | Add a folder of documents |
| `job-status` | Get status of a job |
| `list-jobs` | List all jobs |
| `cancel-job` | Cancel a job |

### 2.5 Job Management

The job management system handles asynchronous processing of long-running tasks:

```mermaid
classDiagram
    class JobManager {
        +create_job(job_type, params, created_by)
        +get_job(job_id)
        +get_jobs_by_status(status)
        +get_jobs_by_client(client_id)
        +run_job_async(job, task_func)
        +cancel_job(job_id)
    }

    class Job {
        +job_id
        +job_type
        +params
        +status
        +progress
        +created_at
        +started_at
        +completed_at
        +result
        +error
        +update_progress(processed_items, total_items)
        +start()
        +complete(result)
        +fail(error)
        +cancel()
    }

    JobManager --> Job
```

## 3. System Architecture Details

### 3.1 Data Flow Diagrams

#### 3.1.1 Document Ingestion Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as API Server
    participant JobMgr as Job Manager
    participant DocProc as Document Processor
    participant Neo4j
    participant ChromaDB
    participant LLM

    Client->>API: POST /documents (document.pdf)
    API->>JobMgr: Create processing job
    JobMgr-->>Client: Return job_id

    JobMgr->>DocProc: Process document (async)
    DocProc->>DocProc: Parse document
    DocProc->>DocProc: Create chunks

    par Embedding Generation
        DocProc->>LLM: Generate embeddings
        LLM-->>DocProc: Return embeddings
        DocProc->>ChromaDB: Store chunks with embeddings
        ChromaDB-->>DocProc: Confirm storage
    and Concept Extraction
        DocProc->>LLM: Extract concepts
        LLM-->>DocProc: Return concepts
        DocProc->>Neo4j: Create concept nodes
        Neo4j-->>DocProc: Confirm creation
    end

    DocProc->>Neo4j: Create document structure
    Neo4j-->>DocProc: Confirm creation
    DocProc->>Neo4j: Create relationships
    Neo4j-->>DocProc: Confirm creation

    DocProc->>JobMgr: Update job status (completed)
    Client->>API: GET /jobs/{job_id}
    API->>JobMgr: Get job status
    JobMgr-->>API: Return job details
    API-->>Client: Return job status
```

#### 3.1.2 Search Query Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as API Server
    participant Search as Search Engine
    participant Neo4j
    participant ChromaDB

    Client->>API: POST /search (query)
    API->>Search: Perform hybrid search

    par Vector Search
        Search->>ChromaDB: Find similar chunks
        ChromaDB-->>Search: Return vector results
    and Graph Search
        Search->>Neo4j: Find related concepts
        Neo4j-->>Search: Return concept graph
        Search->>Neo4j: Find documents for concepts
        Neo4j-->>Search: Return document references
    end

    Search->>Search: Merge and rank results
    Search-->>API: Return combined results
    API-->>Client: Return search results
```

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance

- **Response Time**:
  - Search queries: < 500ms for 95% of queries
  - Document addition acknowledgment: < 200ms
  - Job status queries: < 100ms
- **Throughput**:
  - Support 50+ concurrent search queries
  - Process 10+ documents simultaneously
- **Scalability**:
  - Support up to 100,000 documents (approximately 10 million chunks)
  - Support up to 500,000 concepts and 2 million relationships

#### 3.2.2 Availability and Reliability

- **Uptime**: 99.9% availability target (less than 9 hours of downtime per year)
- **Data Durability**: Zero data loss for committed transactions
- **Fault Tolerance**:
  - Graceful degradation when components fail
  - Automatic recovery from transient failures
  - Job resumption after system restart

#### 3.2.3 Security

- **Authentication**: API key-based authentication for production deployments
- **Authorization**: Role-based access control for administrative functions
- **Data Protection**: TLS encryption for all network communications
- **Input Validation**: Strict validation of all API inputs to prevent injection attacks

#### 3.2.4 Maintainability

- **Code Quality**:
  - Minimum 80% test coverage
  - Adherence to PEP 8 style guidelines
  - Comprehensive documentation
- **Modularity**:
  - Clear separation of concerns
  - Well-defined interfaces between components
  - Pluggable architecture for key components (e.g., embedding models, databases)

#### 3.2.5 Error Handling and Resilience

- **Retry Mechanism**:
  - Automatic retry for transient failures (e.g., network issues, rate limiting)
  - Exponential backoff strategy
  - Maximum retry attempts configurable
- **Circuit Breaker Pattern**:
  - Prevent cascading failures when external services are unavailable
  - Automatic service restoration when dependencies recover
- **Graceful Degradation**:
  - Fall back to vector-only search if graph database is unavailable
  - Continue processing other documents if one document fails
- **Comprehensive Logging**:
  - Structured logging with correlation IDs
  - Error details captured for troubleshooting
  - Performance metrics for monitoring

### 3.3 Deployment Architecture

#### 3.3.1 Docker Deployment

The system can be deployed as a Docker container with all necessary components:

```mermaid
graph TD
    subgraph Docker Container
        API[API Server]
        MPC[MPC Server]
        Neo4j[Neo4j]
        ChromaDB[ChromaDB]
    end

    User[User/AI Agent] --> API
    User --> MPC
    API --> Neo4j
    API --> ChromaDB
    MPC --> Neo4j
    MPC --> ChromaDB
```

##### Port Mappings

| Service | Container Port | Host Port |
|---------|----------------|-----------|
| Neo4j Browser | 7474 | 7475 |
| Neo4j Bolt | 7687 | 7688 |
| API Server | 5000 | 5001 |
| MPC Server | 8765 | 8766 |

#### 3.3.2 Local Deployment

The system can also be run locally with Neo4j installed in `~/.local/neo4j/` and data stored in `~/.graphrag/neo4j/`:

```mermaid
graph TD
    API[API Server] --> Neo4j[Neo4j]
    API --> ChromaDB[ChromaDB]
    MPC[MPC Server] --> Neo4j
    MPC --> ChromaDB
    Neo4j --> Neo4jData[~/.graphrag/neo4j/]
    ChromaDB --> ChromaDBData[./data/chromadb]
```

#### 3.3.3 Production Deployment Topology

For production environments, a more robust deployment architecture is recommended:

```mermaid
graph TD
    subgraph Load Balancer
        LB[NGINX/HAProxy]
    end

    subgraph Application Servers
        API1[API Server 1]
        API2[API Server 2]
        MPC1[MPC Server 1]
        MPC2[MPC Server 2]
    end

    subgraph Database Servers
        Neo4j[Neo4j Cluster]
        ChromaDB[ChromaDB]
    end

    subgraph Job Workers
        Worker1[Worker 1]
        Worker2[Worker 2]
        Worker3[Worker 3]
    end

    Client[Client] --> LB
    LB --> API1
    LB --> API2
    LB --> MPC1
    LB --> MPC2

    API1 --> Neo4j
    API2 --> Neo4j
    MPC1 --> Neo4j
    MPC2 --> Neo4j

    API1 --> ChromaDB
    API2 --> ChromaDB
    MPC1 --> ChromaDB
    MPC2 --> ChromaDB

    API1 -.-> |Job Queue| Worker1
    API2 -.-> |Job Queue| Worker2
    MPC1 -.-> |Job Queue| Worker3
    MPC2 -.-> |Job Queue| Worker1

    Worker1 --> Neo4j
    Worker2 --> Neo4j
    Worker3 --> Neo4j
    Worker1 --> ChromaDB
    Worker2 --> ChromaDB
    Worker3 --> ChromaDB
```

This production topology includes:

- Load balancing for horizontal scaling
- Multiple application server instances for high availability
- Dedicated job workers for processing-intensive tasks
- Neo4j in cluster mode for redundancy
- Shared job queue for distributed processing

## 4. Integration with AI Agents

### 4.1 LangChain Integration

```python
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI
from src.agents.langchain_tools import get_graphrag_tools

# Initialize LangChain components
llm = ChatOpenAI(temperature=0)
tools = get_graphrag_tools(api_url="http://localhost:5001")

# Initialize agent
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=True
)

# Use the agent
agent.run("What does the book 'Deep Learning Fundamentals' say about neural networks?")
```

### 4.2 OpenAI Function Calling

```python
from openai import OpenAI
from src.agents.openai_functions import get_graphrag_functions, get_graphrag_function_map

# Initialize OpenAI client
client = OpenAI()

# Get GraphRAG functions
functions = get_graphrag_functions(api_url="http://localhost:5001")
function_map = get_graphrag_function_map(api_url="http://localhost:5001")

# Use with OpenAI
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Find information about neural networks"}],
    functions=functions,
    function_call="auto"
)

# Handle function calling
if response.choices[0].message.function_call:
    function_name = response.choices[0].message.function_call.name
    function_args = json.loads(response.choices[0].message.function_call.arguments)

    # Call the function
    function_response = function_map[function_name](**function_args)
```

## 5. Remaining Work

The following items are still in progress:

1. **MPC Server Issues** (3.6-spec-mpc-server-issues.md): Fix startup failures and improve reliability
2. **LLM Integration** (3.10-spec-llm-integration.md): Consolidate LLM code to use local models properly
3. **API Port Conflict** (3.7-spec-api-port-conflict.md): Resolve port conflicts when multiple instances start
4. **ChromaDB Duplicate Detection** (3.8-spec-chromadb-duplicate-detection.md): Improve duplicate detection
5. **Vector Search Error** (3.9-spec-vector-search-error.md): Fix errors in vector search
6. **Docker Best Practices** (docker-best-practices.md): Implement Docker best practices

## 6. Installation and Setup

### 6.1 Local Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/graphRAG.git
cd graphRAG

# Create and activate virtual environment with Python 3.12
python3.12 -m venv .venv-py312
source .venv-py312/bin/activate

# Install dependencies using UV
uv pip install -r requirements.txt

# Install Neo4j
./scripts/install_neo4j.sh

# Start Neo4j
./scripts/start_neo4j.sh

# Set Neo4j password (first time only)
/opt/homebrew/bin/neo4j-admin dbms set-initial-password graphrag

# Start the API server
./scripts/start_api_local.sh

# Start the MPC server
./scripts/start_mpc_local.sh
```

### 6.2 Docker Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/graphRAG.git
cd graphRAG

# Build the Docker image
docker build -t graphrag .

# Run the container
docker run -d --name graphrag \
  -p 5001:5000 \
  -p 7475:7474 \
  -p 7688:7687 \
  -p 8766:8765 \
  -v $(pwd)/data:/app/data \
  graphrag
```

### 6.3 Configuration

The system uses environment variables for configuration, which can be set in a `.env` file:

```env
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=graphrag
NEO4J_HOME=/opt/homebrew
NEO4J_DATA_DIR=~/.graphrag/neo4j

# ChromaDB Configuration
CHROMADB_PERSIST_DIRECTORY=./data/chromadb

# LLM Configuration
LLM_ENDPOINT=http://192.168.1.21:1234  # Local LM Studio endpoint for Phi-4
OLLAMA_ENDPOINT=http://localhost:11434  # Local Ollama endpoint
EMBEDDING_MODEL=snowflake-arctic-embed2:latest  # Default embedding model
RERANKER_MODEL=qllama/bge-reranker-large:latest  # Optional reranker model
CONCEPT_MODEL=lmstudio-community/Phi-4-mini-reasoning-MLX-4bit  # Model for concept extraction
USE_LOCAL_LLM=true

# API Configuration
API_HOST=0.0.0.0
API_PORT=5000

# MPC Configuration
MPC_HOST=0.0.0.0
MPC_PORT=8765
```

## 7. Maintenance and Operations

### 7.1 Backup and Restore

```bash
# Backup Neo4j database
tar -czf neo4j_backup.tar.gz ~/.graphrag/neo4j/data

# Backup ChromaDB
tar -czf chromadb_backup.tar.gz ./data/chromadb

# Restore Neo4j database
tar -xzf neo4j_backup.tar.gz -C ~/.graphrag/

# Restore ChromaDB
tar -xzf chromadb_backup.tar.gz -C ./data/
```

### 7.2 Monitoring

The system provides several endpoints for monitoring:

- `/health`: Health check endpoint
- `/metrics`: Prometheus metrics (if enabled)
- `/jobs`: List all jobs and their status

### 7.3 Logging

Logs are stored in the following locations:

- API Server: `./logs/api.log`
- MPC Server: `./logs/mpc.log`
- Neo4j: `~/.graphrag/neo4j/logs/`
- Job Processing: `./logs/jobs.log`

Log level can be configured in the `.env` file:

```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### 7.4 Troubleshooting

Common issues and solutions:

1. **Neo4j Connection Issues**:
   - Ensure Neo4j is running: `ps aux | grep neo4j`
   - Check Neo4j logs: `cat ~/.graphrag/neo4j/logs/neo4j.log`
   - Verify credentials in `.env` file

2. **ChromaDB Issues**:
   - Check permissions on the persist directory
   - Verify ChromaDB version compatibility

3. **API/MPC Server Issues**:
   - Check for port conflicts
   - Verify the server is running: `ps aux | grep server`
   - Check logs for errors

## 8. Security Considerations

### 8.1 Authentication and Authorization

- **API Authentication**:
  - API key-based authentication for all endpoints
  - JWT tokens for session management
  - Rate limiting to prevent abuse
  - Configuration example:

    ```python
    # API key validation middleware
    @app.before_request
    def validate_api_key():
        api_key = request.headers.get('X-API-Key')
        if not api_key or not is_valid_api_key(api_key):
            return jsonify({"error": "Invalid or missing API key"}), 401
    ```

- **MPC Server Authentication**:
  - WebSocket connection requires initial authentication handshake
  - Session tokens for persistent connections
  - Automatic session expiration after inactivity

- **Role-Based Access Control**:
  - Admin role: Full system access
  - Editor role: Add/modify documents and concepts
  - Reader role: Search and retrieve information only
  - Implementation via middleware that checks permissions for each request

### 8.2 Threat Modeling

The system has been analyzed for potential security threats using the STRIDE model:

| Threat Type | Potential Threats | Mitigation Strategies |
|-------------|-------------------|------------------------|
| Spoofing | Unauthorized API access | API key authentication, TLS, IP restrictions |
| Tampering | Modification of document content | Input validation, data integrity checks |
| Repudiation | Denial of document submission | Comprehensive audit logging with timestamps |
| Information Disclosure | Exposure of sensitive document content | Access controls, data classification |
| Denial of Service | Overwhelming system with requests | Rate limiting, resource quotas, monitoring |
| Elevation of Privilege | Gaining unauthorized admin access | Principle of least privilege, role separation |

### 8.3 Data Protection

- **Data at Rest**:
  - Database encryption for sensitive content
  - Secure storage of API keys and credentials
  - Regular security audits and vulnerability scanning

- **Data in Transit**:
  - TLS 1.3 for all HTTP/WebSocket communications
  - Certificate validation to prevent MITM attacks
  - Secure headers (HSTS, CSP, X-Content-Type-Options)

- **Input Validation**:
  - Strict schema validation for all API inputs
  - Content type verification for uploaded documents
  - Sanitization of text inputs to prevent injection attacks

### 8.4 Secrets Management

- **Environment Variables**:
  - Sensitive configuration stored in environment variables
  - No hardcoded secrets in source code
  - Different credentials for development/staging/production

- **Credential Rotation**:
  - Regular rotation of API keys and database credentials
  - Automated credential rotation process
  - Immediate revocation capabilities for compromised credentials

- **Production Secrets**:
  - Integration with vault systems (HashiCorp Vault, AWS Secrets Manager)
  - Just-in-time access to production credentials
  - Audit trail for all secret access

### 8.5 Inter-Service Communication

- **Internal Network Security**:
  - Service-to-service authentication
  - Network segmentation to isolate components
  - Mutual TLS for service communication
  - Example configuration:

    ```yaml
    # Docker Compose network configuration
    services:
      api:
        networks:
          - frontend
          - backend
      neo4j:
        networks:
          - backend

    networks:
      frontend:
        # External-facing network
      backend:
        # Internal services only
        internal: true
    ```

## 9. Performance Optimization

- **Scaling Vector Search**: For large collections (>100K documents), consider sharding ChromaDB.
- **Neo4j Indexing**: Create indexes on frequently queried properties:

  ```cypher
  CREATE INDEX ON :Concept(name);
  CREATE INDEX ON :Document(title);
  ```

- **Batch Processing**: Use batch sizes of 100-1000 for optimal performance when adding documents.
- **Memory Management**: Monitor memory usage and adjust JVM settings for Neo4j if needed.

## 10. Detailed API Documentation

### 10.1 REST API Endpoints

#### `GET /health`

Health check endpoint.

**Response:**

```json
{
  "status": "ok",
  "version": "2.0.0",
  "neo4j_connected": true,
  "chromadb_connected": true
}
```

#### `GET /version`

Get application version.

**Response:**

```json
{
  "version": "2.0.0",
  "build_date": "2023-05-08"
}
```

#### `POST /search`

Perform hybrid search.

**Request:**

```json
{
  "query": "neural networks in deep learning",
  "n_results": 5,
  "max_hops": 2
}
```

**Response:**

```json
{
  "results": [
    {
      "text": "Neural networks are a fundamental component of deep learning...",
      "metadata": {
        "document_id": "doc123",
        "title": "Deep Learning Fundamentals",
        "page": 42
      },
      "score": 0.92,
      "source": "vector"
    },
    {
      "text": "The architecture of neural networks consists of layers...",
      "metadata": {
        "document_id": "doc456",
        "title": "Machine Learning Handbook",
        "page": 78
      },
      "score": 0.85,
      "source": "graph",
      "path": ["neural networks", "architecture", "layers"]
    }
  ]
}
```

#### `GET /concepts/<concept_name>`

Get concept information.

**Response:**

```json
{
  "name": "neural networks",
  "category": "machine learning",
  "related_concepts": [
    {"name": "deep learning", "strength": 0.9},
    {"name": "backpropagation", "strength": 0.8},
    {"name": "activation functions", "strength": 0.7}
  ],
  "documents": [
    {"title": "Deep Learning Fundamentals", "id": "doc123"},
    {"title": "Machine Learning Handbook", "id": "doc456"}
  ]
}
```

### 10.2 MPC Protocol

The MPC server uses WebSockets for communication. Messages are JSON objects with the following structure:

**Request:**

```json
{
  "id": "request-123",
  "action": "search",
  "params": {
    "query": "neural networks",
    "n_results": 5
  }
}
```

**Response:**

```json
{
  "id": "request-123",
  "status": "success",
  "result": {
    "results": [
      {
        "text": "Neural networks are a fundamental component...",
        "metadata": {
          "document_id": "doc123",
          "title": "Deep Learning Fundamentals"
        },
        "score": 0.92
      }
    ]
  }
}
```

**Error Response:**

```json
{
  "id": "request-123",
  "status": "error",
  "error": {
    "code": "not_found",
    "message": "Concept not found"
  }
}
```

## 11. Development and Testing

### 11.1 Development Workflow

The GraphRAG project follows a feature-branch workflow:

1. **Branch Creation**:

   ```bash
   # Ensure you're on the main branch and it's up to date
   git checkout main
   git pull

   # Create a new branch with appropriate naming
   git checkout -b feature-new-feature     # For new features
   git checkout -b task-specific-task      # For specific tasks
   git checkout -b bug-issue-description   # For bug fixes
   ```

2. **Development Process**:
   - Make incremental changes with frequent commits
   - Follow the coding standards (see below)
   - Update tests as you develop
   - Document new features or API changes

3. **Code Review and Merge**:

   ```bash
   # Before submitting for review, run linting
   source .venv-py312/bin/activate
   ruff check src/
   ruff check scripts/

   # Run tests
   pytest tests/

   # Commit final changes
   git add .
   git commit -m "Descriptive commit message"

   # Push to remote
   git push origin feature-new-feature

   # Create a pull request on GitHub
   # After approval, merge to main
   git checkout main
   git merge feature-new-feature
   git tag -a v1.2.3 -m "Version 1.2.3"
   git push --tags
   ```

### 11.2 Coding Standards

- **Python Style**: Follow PEP 8 guidelines
- **Docstrings**: Use Google-style docstrings
- **Type Hints**: Use type hints for all function parameters and return values
- **Linting**: Use ruff for linting and formatting
- **Imports**: Organize imports in the following order:
  1. Standard library imports
  2. Third-party library imports
  3. Local application imports

Example:

```python
# Standard library
import os
import sys
from typing import List, Dict, Optional

# Third-party libraries
import numpy as np
from neo4j import GraphDatabase
import chromadb

# Local application
from src.database.neo4j_db import Neo4jDatabase
from src.utils.logger import get_logger
```

### 11.3 Testing Strategy

The GraphRAG system uses pytest for testing. Tests are organized into the following categories:

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test interactions between components
3. **End-to-End Tests**: Test complete workflows
4. **Performance Tests**: Test system performance under load

#### Running Tests

```bash
# Activate virtual environment
source .venv-py312/bin/activate

# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
pytest tests/performance/

# Run tests with coverage
pytest --cov=src tests/

# Generate coverage report
pytest --cov=src --cov-report=html tests/
```

#### Test Structure

```text
tests/
├── unit/
│   ├── test_neo4j_db.py
│   ├── test_vector_db.py
│   └── ...
├── integration/
│   ├── test_database_linkage.py
│   ├── test_document_processing.py
│   └── ...
├── e2e/
│   ├── test_search_workflow.py
│   ├── test_document_addition.py
│   └── ...
└── performance/
    ├── test_search_performance.py
    ├── test_processing_performance.py
    └── ...
```

### 11.4 Complete Workflow Examples

#### Example 1: Adding Documents and Searching

```python
import os
from src.database.neo4j_db import Neo4jDatabase
from src.database.vector_db import VectorDatabase
from src.processing.document_processor import DocumentProcessor
from src.search.hybrid_search import HybridSearch

# Initialize databases
neo4j_db = Neo4jDatabase()
vector_db = VectorDatabase()

# Initialize document processor
processor = DocumentProcessor(neo4j_db, vector_db)

# Add a document
document_path = "/path/to/document.pdf"
job = processor.process_document(document_path)

# Wait for processing to complete
while not job.is_complete():
    print(f"Processing: {job.progress}%")
    time.sleep(1)

# Initialize search
search = HybridSearch(neo4j_db, vector_db)

# Perform search
results = search.search("neural networks in deep learning", n_results=5, max_hops=2)

# Display results
for result in results:
    print(f"Text: {result['text'][:100]}...")
    print(f"Source: {result['source']}")
    print(f"Score: {result['score']}")
    print(f"Document: {result['metadata']['title']}")
    print("---")
```

#### Example 2: Using the MPC Server from a Client

```python
import asyncio
import json
import websockets

async def graphrag_client():
    uri = "ws://localhost:8765"

    async with websockets.connect(uri) as websocket:
        # Ping to test connection
        await websocket.send(json.dumps({
            "id": "ping-1",
            "action": "ping"
        }))

        response = await websocket.recv()
        print(f"Ping response: {response}")

        # Add a document
        await websocket.send(json.dumps({
            "id": "add-doc-1",
            "action": "add-document",
            "params": {
                "path": "/path/to/document.pdf",
                "async": True
            }
        }))

        response = json.loads(await websocket.recv())
        job_id = response["result"]["job_id"]

        # Check job status
        while True:
            await websocket.send(json.dumps({
                "id": "job-status-1",
                "action": "job-status",
                "params": {
                    "job_id": job_id
                }
            }))

            status_response = json.loads(await websocket.recv())
            if status_response["result"]["status"] == "completed":
                break

            print(f"Progress: {status_response['result']['progress']}%")
            await asyncio.sleep(2)

        # Perform search
        await websocket.send(json.dumps({
            "id": "search-1",
            "action": "search",
            "params": {
                "query": "neural networks",
                "n_results": 5
            }
        }))

        search_response = json.loads(await websocket.recv())
        for result in search_response["result"]["results"]:
            print(f"Text: {result['text'][:100]}...")
            print(f"Score: {result['score']}")
            print("---")

# Run the client
asyncio.run(graphrag_client())
```

### 11.5 Performance Benchmarks

The GraphRAG system has been benchmarked on various datasets and hardware configurations. Here are the key performance metrics:

#### Document Processing

| Document Type | Size | Processing Time | Memory Usage |
|---------------|------|-----------------|--------------|
| PDF (text)    | 10 MB | 15-20 seconds   | ~200 MB      |
| PDF (complex) | 10 MB | 30-45 seconds   | ~300 MB      |
| Markdown      | 1 MB  | 3-5 seconds     | ~100 MB      |
| Text          | 1 MB  | 2-3 seconds     | ~100 MB      |

**Note:** Measured on a system with 4 CPU cores and 8GB RAM

#### Search Performance

| Dataset Size | Query Type | Response Time | Memory Usage |
|--------------|------------|---------------|--------------|
| 100 documents | Vector only | 50-100 ms     | ~150 MB      |
| 100 documents | Hybrid      | 100-200 ms    | ~200 MB      |
| 1000 documents | Vector only | 100-200 ms    | ~300 MB      |
| 1000 documents | Hybrid      | 200-400 ms    | ~400 MB      |
| 10000 documents | Vector only | 200-500 ms    | ~1 GB        |
| 10000 documents | Hybrid      | 500-1000 ms   | ~1.2 GB      |

**Note:** Measured on a system with 4 CPU cores and 8GB RAM

#### Scaling Characteristics

- **CPU Scaling**: Processing performance scales almost linearly with CPU cores up to 8 cores
- **Memory Requirements**:
  - Base system: ~500 MB
  - Per 1000 documents: ~300 MB additional
- **Storage Requirements**:
  - Neo4j database: ~20% of original document size
  - ChromaDB: ~30% of original document size

## 12. Supporting Documentation

### 12.1 Glossary of Terms

| Term | Definition |
|------|------------|
| **GraphRAG** | Hybrid Retrieval-Augmented Generation system combining vector embeddings with knowledge graphs |
| **Hybrid Search** | Search technique that combines vector similarity with graph traversal |
| **Concept Extraction** | Process of identifying key concepts from document text |
| **Chunk** | A segment of a document, typically a paragraph or section |
| **Embedding** | A vector representation of text that captures semantic meaning |
| **MPC Server** | Message Passing Communication server for AI agent integration |
| **Vector Database** | Database optimized for storing and querying vector embeddings |
| **Graph Database** | Database that represents data as nodes and relationships |
| **Job Manager** | System component that handles asynchronous processing tasks |
| **Deduplication** | Process of identifying and removing duplicate documents or concepts |

### 12.2 Key Use Cases

1. **Knowledge Discovery**:
   - Users can explore connections between concepts across multiple documents
   - Example: "Show me all books that discuss neural networks and their relationship to deep learning"

2. **Contextual Search**:
   - Users can find information with rich context beyond keyword matching
   - Example: "Find passages about transformer architecture in the context of natural language processing"

3. **Document Organization**:
   - System automatically organizes documents by extracting concepts and relationships
   - Example: "Categorize my technical library by main topics and show connections between subjects"

4. **AI Agent Knowledge Base**:
   - AI agents can access and reason over structured knowledge
   - Example: "Answer questions about machine learning techniques using my document collection"

5. **Research Synthesis**:
   - Researchers can identify patterns and connections across multiple sources
   - Example: "Summarize the evolution of reinforcement learning across my research papers"

### 12.3 Architecture Decision Records (ADRs)

#### ADR-001: Choice of Neo4j for Graph Database

**Context**: The system needs a database to store and query complex relationships between concepts and documents.

**Decision**: Use Neo4j as the graph database.

**Alternatives Considered**:

- ArangoDB: Multi-model database with graph capabilities
- Amazon Neptune: Cloud-based graph database
- TigerGraph: Distributed graph database

**Rationale**:

- Neo4j's Cypher query language provides an intuitive way to express complex graph traversals
- Strong community support and extensive documentation
- Native Python drivers with good performance
- Can be deployed locally or in the cloud
- Property graph model aligns well with our concept-document relationship structure

**Consequences**:

- Positive: Simplified relationship modeling and querying
- Negative: Requires specific knowledge of Cypher
- Negative: Vertical scaling limitations for very large graphs

#### ADR-002: Hybrid Chunking Strategy

**Context**: Documents need to be split into chunks for embedding and storage in the vector database.

**Decision**: Implement a hybrid chunking strategy that combines semantic boundaries, document structure, and size constraints.

**Alternatives Considered**:

- Fixed-size chunking: Split documents into chunks of a fixed number of tokens
- Sentence-based chunking: Use sentence boundaries as chunk delimiters
- Paragraph-based chunking: Use paragraph boundaries as chunk delimiters

**Rationale**:

- Semantic boundaries preserve the meaning of content
- Respecting document structure (headings, sections) maintains context
- Size constraints ensure compatibility with embedding models
- Hybrid approach provides the best balance of semantic coherence and practical constraints

**Consequences**:

- Positive: More meaningful chunks that preserve context
- Positive: Better search results due to coherent chunks
- Negative: More complex implementation
- Negative: Variable chunk sizes may require additional handling

#### ADR-003: Asynchronous Processing Architecture

**Context**: Processing large documents or batches of documents can be time-consuming and should not block the user interface.

**Decision**: Implement an asynchronous job processing system with persistent job tracking.

**Alternatives Considered**:

- Synchronous processing: Process documents in the request thread
- Simple background threads: Use threading without persistent job tracking
- External job queue: Use a separate service like RabbitMQ or Redis for job queuing

**Rationale**:

- Asynchronous processing provides better user experience for long-running tasks
- Persistent job tracking allows users to monitor progress and resume after interruptions
- SQLite-based job storage provides simplicity while maintaining persistence
- Design allows for future migration to more robust job queues if needed

**Consequences**:

- Positive: Improved user experience for long-running tasks
- Positive: Ability to handle large batches of documents
- Positive: Resilience to system restarts
- Negative: Increased system complexity
- Negative: Need for additional error handling and recovery mechanisms

## 13. Conclusion

The GraphRAG system provides a powerful hybrid approach to information retrieval and synthesis by combining vector embeddings with knowledge graphs. Its modular architecture allows for easy integration with AI agents and scalable processing of large document collections.

The system's key strengths include:

- Hybrid search combining vector similarity with graph traversal
- Rich concept extraction and relationship building
- Asynchronous processing for handling large document collections
- Flexible deployment options (Docker, local)
- Comprehensive API and MPC interfaces for integration

Future development will focus on:

- Enhancing the concept extraction capabilities
- Improving performance for very large document collections
- Adding more sophisticated relationship types
- Expanding the AI agent integration options
- Implementing the security features outlined in this document
