# Bug Report: Add Document API Endpoint

## Description
The `/documents` API endpoint is failing with a 500 error because the `add_document_to_graphrag` function signature in the API server doesn't match the actual function in the `scripts/add_document.py` file.

## Steps to Reproduce
1. Run the regression tests with `python -m tests.regression.run_all_tests`
2. Observe that tests 3-6 fail with a 500 error when trying to add a document

## Expected Behavior
The `/documents` endpoint should successfully add a document to the GraphRAG system.

## Actual Behavior
The endpoint returns a 500 error because the `add_document_to_graphrag` function in the API server is missing the required `duplicate_detector` parameter.

## Fix Required
Update the `add_document` function in `src/api/server.py` to initialize a `DuplicateDetector` instance and pass it to the `add_document_to_graphrag` function:

```python
from src.processing.duplicate_detector import DuplicateDetector

@app.route('/documents', methods=['POST'])
def add_document():
    """
    Add a document to the GraphRAG system.

    Request body:
        text (str): Document text
        metadata (dict, optional): Document metadata

    Returns:
        Status of the operation
    """
    data = request.json

    if not data or 'text' not in data:
        return jsonify({'error': 'Missing required parameter: text'}), 400

    text = data['text']
    metadata = data.get('metadata', {})

    try:
        # Import here to avoid circular imports
        from scripts.add_document import add_document_to_graphrag
        from src.processing.duplicate_detector import DuplicateDetector

        # Initialize duplicate detector
        duplicate_detector = DuplicateDetector(vector_db)

        result = add_document_to_graphrag(
            text=text,
            metadata=metadata,
            neo4j_db=neo4j_db,
            vector_db=vector_db,
            duplicate_detector=duplicate_detector
        )

        return jsonify({
            'status': 'success',
            'message': 'Document added successfully',
            'document_id': result.get('document_id'),
            'entities': result.get('entities', []),
            'relationships': result.get('relationships', [])
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

## Additional Notes
- This is a critical bug that prevents all document-related functionality from working
- The fix is straightforward and should be implemented immediately