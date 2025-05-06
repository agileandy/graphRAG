"""
Example of using GraphRAG with OpenAI function calling.
"""
import os
import sys
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()

# Import OpenAI
import openai

# Import GraphRAG functions
from src.agents.openai_functions import get_graphrag_functions, get_graphrag_function_map

def main():
    """
    Main function to demonstrate using GraphRAG with OpenAI function calling.
    """
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable is not set.")
        print("Please set it in your .env file or export it in your shell.")
        return
    
    # Set OpenAI API key
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
    # Get GraphRAG functions and function map
    functions = get_graphrag_functions()
    function_map = get_graphrag_function_map()
    
    # Initialize conversation
    messages = [
        {"role": "system", "content": "You are a helpful assistant that can search and explore the GraphRAG knowledge base. Use the available functions to help the user find information."}
    ]
    
    # Run interactive chat
    print("\nGraphRAG OpenAI Function Calling")
    print("================================")
    print("Type 'exit' to quit.")
    print()
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ["exit", "quit", "q"]:
            break
        
        # Add user message to conversation
        messages.append({"role": "user", "content": user_input})
        
        try:
            # Call OpenAI API with function calling
            response = openai.chat.completions.create(
                model="gpt-4-turbo",  # or another model that supports function calling
                messages=messages,
                functions=functions,
                function_call="auto"
            )
            
            # Get assistant message
            assistant_message = response.choices[0].message
            
            # Add assistant message to conversation
            messages.append(assistant_message.model_dump())
            
            # Check if function call was requested
            if assistant_message.function_call:
                # Get function name and arguments
                function_name = assistant_message.function_call.name
                function_args = json.loads(assistant_message.function_call.arguments)
                
                # Call the function
                if function_name in function_map:
                    function_response = function_map[function_name](**function_args)
                    
                    # Add function response to conversation
                    messages.append({
                        "role": "function",
                        "name": function_name,
                        "content": json.dumps(function_response)
                    })
                    
                    # Get final response
                    final_response = openai.chat.completions.create(
                        model="gpt-4-turbo",  # or another model that supports function calling
                        messages=messages
                    )
                    
                    # Add final response to conversation
                    final_message = final_response.choices[0].message
                    messages.append(final_message.model_dump())
                    
                    # Print final response
                    print(f"Assistant: {final_message.content}")
                else:
                    print(f"Error: Function '{function_name}' not found.")
            else:
                # Print assistant response
                print(f"Assistant: {assistant_message.content}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()