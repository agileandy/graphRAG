# Managing Docker Containers in the Development Lifecycle

## 1. Development Environment

### Local Development Setup

- **Docker Compose for Development**:
  - Use `docker-compose.yml` with development-specific configurations
  - Mount source code as volumes for live code editing
  - Enable debug ports and development tools

```yaml
# Example docker-compose.dev.yml
services:
  graphrag:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - ./src:/app/src  # Mount source code for live editing
      - ./scripts:/app/scripts
      - ./data:/app/data
    environment:
      - DEBUG=true
      - LOG_LEVEL=debug
    ports:
      - "7475:7474"  # Neo4j Browser
      - "7688:7687"  # Neo4j Bolt
      - "5001:5000"  # API Server
      - "8766:8765"  # MCP Server
```

- **Development Workflow**:
  ```bash
  # Start development environment
  docker-compose -f docker-compose.dev.yml up -d

  # View logs
  docker-compose -f docker-compose.dev.yml logs -f

  # Rebuild after Dockerfile changes
  docker-compose -f docker-compose.dev.yml up -d --build

  # Stop containers without removing them
  docker-compose -f docker-compose.dev.yml stop

  # Stop and remove containers
  docker-compose -f docker-compose.dev.yml down
  ```

### Development Best Practices

- **Use Multi-stage Builds**: Separate build dependencies from runtime dependencies
- **Layer Caching**: Order Dockerfile commands to maximize cache usage
- **Development Tools**: Include debugging tools in development images
- **Hot Reloading**: Configure applications for automatic reloading when code changes

## 2. Testing Environment

### Automated Testing

- **Test-specific Compose File**:
  ```yaml
  # docker-compose.test.yml
  services:
    graphrag:
      build:
        context: .
        dockerfile: Dockerfile.test
      environment:
        - TESTING=true
        - NEO4J_URI=bolt://neo4j-test:7687

    neo4j-test:
      image: neo4j:5.18.1
      environment:
        - NEO4J_AUTH=neo4j/test_password
  ```

- **CI/CD Integration**:
  ```bash
  # Run in CI pipeline
  docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
  ```

### Testing Best Practices

- **Ephemeral Containers**: Create and destroy containers for each test run
- **Isolated Networks**: Use Docker networks to isolate test environments
- **Volume Mounts**: Mount test fixtures and results as volumes
- **Health Checks**: Implement container health checks to ensure services are ready

## 3. Staging Environment

### Pre-production Validation

- **Staging Configuration**:
  ```yaml
  # docker-compose.staging.yml
  services:
    graphrag:
      image: ${REGISTRY}/graphrag:${TAG}
      environment:
        - ENVIRONMENT=staging
        - LOG_LEVEL=info
      restart: unless-stopped
  ```

- **Deployment to Staging**:
  ```bash
  # Deploy to staging
  TAG=$(git rev-parse --short HEAD)
  REGISTRY=your-registry.com

  # Build and push
  docker build -t ${REGISTRY}/graphrag:${TAG} .
  docker push ${REGISTRY}/graphrag:${TAG}

  # Deploy
  docker-compose -f docker-compose.staging.yml up -d
  ```

### Staging Best Practices

- **Mirror Production**: Make staging as similar to production as possible
- **Realistic Data**: Use anonymized production data or realistic synthetic data
- **Performance Testing**: Run load tests in staging environment
- **Monitoring**: Implement the same monitoring as production

## 4. Production Environment

### Production Deployment

- **Production Configuration**:
  ```yaml
  # docker-compose.prod.yml
  services:
    graphrag:
      image: ${REGISTRY}/graphrag:${TAG}
      environment:
        - ENVIRONMENT=production
        - LOG_LEVEL=warn
      restart: always
      deploy:
        replicas: 2
        update_config:
          parallelism: 1
          delay: 10s
        restart_policy:
          condition: on-failure
  ```

- **Deployment Strategies**:
  - Blue-Green Deployment: Run two identical environments, switch traffic
  - Rolling Updates: Update containers one at a time
  - Canary Releases: Route a percentage of traffic to new version

### Production Best Practices

- **Immutable Infrastructure**: Never modify running containers; replace them
- **Resource Limits**: Set memory and CPU limits for containers
- **Secrets Management**: Use Docker secrets or external vault for sensitive data
- **Logging and Monitoring**: Implement comprehensive logging and monitoring
- **Backup Strategy**: Regular backups of persistent data

## 5. Container Lifecycle Management

### Image Versioning

- **Tagging Strategy**:
  - Use semantic versioning (e.g., `v1.2.3`)
  - Include git commit hash (e.g., `v1.2.3-a1b2c3d`)
  - Tag latest stable version as `latest`
  - Tag development versions as `dev`

- **Image Registry**:
  - Use a private registry for proprietary code
  - Implement access controls and scanning
  - Set up retention policies for old images

### Container Orchestration

- **For Simple Setups**:
  - Docker Compose for single-host deployments
  - Docker Swarm for basic multi-host orchestration

- **For Complex Setups**:
  - Kubernetes for advanced orchestration
  - Helm charts for package management
  - Operators for complex applications

### Maintenance and Updates

- **Regular Updates**:
  - Update base images for security patches
  - Rebuild images periodically
  - Test updates in lower environments first

- **Monitoring and Alerting**:
  - Monitor container health and resource usage
  - Set up alerts for abnormal behavior
  - Implement auto-scaling based on metrics

## 6. Specific Recommendations for GraphRAG

Based on your GraphRAG project, here are specific recommendations:

### Development Workflow

1. **Source Control Integration**:
   ```bash
   # Create a feature branch
   git checkout -b feature/new-feature

   # Make changes to code

   # Build and test locally
   docker-compose -f docker-compose.dev.yml up -d --build

   # Run tests
   docker exec graphrag python -m pytest

   # Commit changes
   git add .
   git commit -m "Add new feature"

   # Push to remote
   git push origin feature/new-feature
   ```

2. **Managing Neo4j Data**:
   - Use named volumes for Neo4j data persistence
   - Implement backup scripts for Neo4j data
   - Create data initialization scripts for fresh environments

3. **ChromaDB Management**:
   - Implement proper error handling for ChromaDB operations
   - Set up regular backups of vector database
   - Monitor ChromaDB performance and resource usage

### Deployment Strategy

1. **Version Tagging**:
   ```bash
   # Tag a release
   git tag -a v2.1.0 -m "Release v2.1.0"
   git push origin v2.1.0

   # Build and tag Docker image
   docker build -t graphrag:v2.1.0 .

   # Push to registry (if using)
   docker push your-registry.com/graphrag:v2.1.0
   ```

2. **Environment-specific Configurations**:
   - Create `.env.dev`, `.env.test`, `.env.prod` files
   - Use Docker Compose environment file option:
     ```bash
     docker-compose --env-file .env.dev up -d
     ```

3. **Continuous Integration**:
   - Set up GitHub Actions or Jenkins pipeline
   - Automate testing and image building
   - Implement vulnerability scanning

## 7. Documentation and Standards

1. **Document Docker Setup**:
   - Create a `DOCKER.md` file explaining the setup
   - Document environment variables and configuration options
   - Include troubleshooting steps for common issues

2. **Standardize Commands**:
   - Create Makefiles or shell scripts for common operations:
     ```bash
     # Example Makefile
     .PHONY: dev test prod

     dev:
         docker-compose -f docker-compose.dev.yml up -d

     test:
         docker-compose -f docker-compose.test.yml up --build

     prod:
         docker-compose -f docker-compose.prod.yml up -d
     ```

3. **Create Onboarding Guide**:
   - Document steps for new developers to set up environment
   - Include common workflows and commands
   - Provide examples of typical development tasks