# Bug 7: Document ID Not Returned in API Response

## Description
The `/documents` API endpoint is successfully adding documents to the GraphRAG system, but it's not returning the document ID in the response when a document is detected as a duplicate.

## Cause
The `add_document_to_graphrag` function in `scripts/add_document.py` returns `None` when a document is detected as a duplicate. The API endpoint in `src/api/server.py` tries to access the `document_id` key from this `None` result, which causes the issue.

## Fix Required
Update the `add_document` function in `src/api/server.py` to handle the case when a document is a duplicate:

1. Check for duplicates before adding the document
2. If the document is a duplicate, return a response with the existing document ID
3. If the document is not a duplicate, return the new document ID

## Implementation
The fix involves modifying the `/documents` endpoint in `src/api/server.py` to:

1. Calculate the document hash and check for duplicates before adding the document
2. Handle the case when `add_document_to_graphrag` returns `None` (for duplicate documents)
3. Return a response with the appropriate document ID in both cases

```python
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

        # Calculate document hash for duplicate checking
        doc_hash = duplicate_detector.generate_document_hash(text)
        metadata_with_hash = metadata.copy()
        metadata_with_hash["hash"] = doc_hash

        # Check for duplicates before adding
        is_dup, existing_doc_id, method = duplicate_detector.is_duplicate(text, metadata_with_hash)

        result = add_document_to_graphrag(
            text=text,
            metadata=metadata,
            neo4j_db=neo4j_db,
            vector_db=vector_db,
            duplicate_detector=duplicate_detector
        )

        if result:
            # Document was added successfully
            return jsonify({
                'status': 'success',
                'message': 'Document added successfully',
                'document_id': result.get('document_id'),
                'entities': result.get('entities', []),
                'relationships': result.get('relationships', [])
            })
        else:
            # Document was a duplicate
            return jsonify({
                'status': 'duplicate',
                'message': 'Document is a duplicate and was not added',
                'document_id': existing_doc_id,
                'duplicate_detection_method': method,
                'entities': [],
                'relationships': []
            })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
```

## Testing
The fix was tested by running the regression test `test_03_add_document.py`, which now successfully retrieves the document ID from the API response, even when the document is a duplicate.

## Status
Fixed
