# Bug Report: Document ID Not Returned in API Response

## Description
The `/documents` API endpoint is successfully adding documents to the GraphRAG system, but it's not returning the document ID in the response. This causes Tests 3 and 6 to fail because they expect a document ID to be returned.

## Steps to Reproduce
1. Run the regression tests with `python -m tests.regression.run_all_tests`
2. Observe that Tests 3 and 6 fail with "Document ID not found in response"

## Expected Behavior
The `/documents` endpoint should return the document ID in the response.

## Actual Behavior
The `document_id` field in the response is `null`.

## Fix Required
Update the `add_document_to_graphrag` function in `scripts/add_document.py` to return the document ID in the result dictionary:

```python
def add_document_to_graphrag(
    text: str,
    metadata: Dict[str, Any],
    neo4j_db: Neo4jDatabase,
    vector_db: VectorDatabase,
    duplicate_detector: DuplicateDetector
) -> Optional[Dict[str, Any]]:
    # ... existing code ...

    # Create a unique ID for the document
    doc_id = f"doc-{uuid.uuid4()}"

    # ... existing code ...

    return {
        "document_id": doc_id,  # Change from "doc_id" to "document_id"
        "entities": entities,
        "relationships": relationships
    }
```

## Additional Notes
- This is a minor issue that doesn't affect the functionality of the system, but it does cause the tests to fail
- The fix is straightforward and should be implemented as soon as possible