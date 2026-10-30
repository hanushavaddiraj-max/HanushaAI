import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import FunctionTool, ToolSet, CodeInterpreterTool
from functions import user_functions
from dotenv import load_dotenv

load_dotenv()
model = os.getenv("MODEL_DEPLOYMENT_NAME")
project_connection_string = os.getenv("PROJECT_CONNECTION_STRING")  


project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=project_connection_string,
)

# Create agent with toolset and process assistant run
with project_client:
    # Initialize agent toolset with user functions and code interpreter
    # [START create_agent_toolset]
    functions = FunctionTool(user_functions)
    
    toolset = ToolSet()
    toolset.add(functions)
   

    agent = project_client.agents.create_agent(
        model=model,
        name="function-calling-assistant",
        instructions="You are a helpful assistant",
        toolset=toolset,
    )
    # [END create_agent_toolset]
    print(f"Created agent, ID: {agent.id}")

    # Create thread for communication
    thread = project_client.agents.create_thread()
    print(f"Created thread, ID: {thread.id}")

    # Create message to thread
    message = project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content="Hello can you please fetch weather information for london?",
    )
    print(f"Created message, ID: {message.id}")

    # Create and process agent run in thread with tools
    # [START create_and_process_run]
    run = project_client.agents.create_and_process_run(thread_id=thread.id, assistant_id=agent.id)
    # [END create_and_process_run]
    print(f"Run finished with status: {run.status}")

    if run.status == "failed":
        print(f"Run failed: {run.last_error}")

    

    # Fetch and log all messages
    messages = project_client.agents.list_messages(thread_id=thread.id)
    print(f"Messages: {messages}")
    print("\n")
    
    #printing the assistant response
    print(f"User information: {messages.data[0].content[0].text.value}")