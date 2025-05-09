1. Test Suite (all via the WEB-API)
   1. Test 1 - Check start and stop works
      1. start all of the services
      2. stop all of the services
   2. Test 2 - check database initialisation works
      1. completely delete datastores (chroma and neo4j - make it as if this was a new installation)
      2. build the databases
   3. Test 3 - Check we can add a document
      1. add a document
      2. check it is in the database
      3. check indexes exist
   4. Test 4 - Check NLP works
      1. check nlp concepts are in the database
      2. check relationships are in the database
   5. Test 5 - Check we can search for a document
      1. search for a document with RAG
      2. search for relationships and concepts
   6. Test 6 - Test deduping
      1. add a document
      2. add it again
      3. check it is not in the database twice or is somehow related to itself or other documents