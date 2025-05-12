"""
Example of using GraphRAG with a LangChain agent.
"""
import os
import sys
from dotenv import load_dotenv
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import GraphRAG tools
from src.agents.langchain_tools import get_graphrag_tools

# Load environment variables
load_dotenv()

def main():
    """
    Main function to demonstrate using GraphRAG with a LangChain agent.
    """
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable is not set.")
        print("Please set it in your .env file or export it in your shell.")
        return

    # Initialize LangChain components
    llm = ChatOpenAI(temperature=0)
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    # Get GraphRAG tools
    tools = get_graphrag_tools()

    # Initialize agent
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=True,
        memory=memory
    )

    # Run interactive chat
    print("\nGraphRAG LangChain Agent")
    print("========================")
    print("Type 'exit' to quit.")
    print()

    while True:
        user_input = input("You: ")

        if user_input.lower() in ["exit", "quit", "q"]:
            break

        try:
            response = agent.run(user_input)
            print(f"Agent: {response}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()