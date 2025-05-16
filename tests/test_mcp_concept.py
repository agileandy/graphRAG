"""
Test script for MPC server concept exploration functionality.
"""
import asyncio
import websockets
import json
import sys

async def test_concept(uri, concept_name="RAG"):
    """Test concept exploration functionality."""
    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("Connected successfully!")
            
            # Prepare concept message
            message = {
                'action': 'concept',
                'concept_name': concept_name
            }
            
            print(f"Exploring concept: '{concept_name}'...")
            await websocket.send(json.dumps(message))
            
            print("Waiting for response...")
            response = await websocket.recv()
            
            print("\nConcept exploration results:")
            response_data = json.loads(response)
            print(json.dumps(response_data, indent=2))
            
            # Now try to get related concepts
            message = {
                'action': 'related-concepts',
                'concept_name': concept_name,
                'max_hops': 2
            }
            
            print(f"\nExploring related concepts to '{concept_name}'...")
            await websocket.send(json.dumps(message))
            
            print("Waiting for response...")
            response = await websocket.recv()
            
            print("\nRelated concepts results:")
            response_data = json.loads(response)
            print(json.dumps(response_data, indent=2))
            
            return True
    except Exception as e:
        print(f"Concept exploration failed: {e}")
        return False

async def main():
    uri = "ws://localhost:8766"
    
    # You can change the concept name here
    concept_name = "RAG"
    
    success = await test_concept(uri, concept_name)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
