import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import AzureAISearchTool, ConnectionType
from dotenv import load_dotenv


load_dotenv()
project_connection_string = os.getenv("PROJECT_CONNECTION_STRING")
model = os.getenv("MODEL_DEPLOYMENT_NAME")
index_name=os.getenv("AI_SEARCH_INDEX_NAME")

project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=project_connection_string,
)

# [START create_agent_with_azure_ai_search_tool]
conn_list = project_client.connections.list()
conn_id = ""
for conn in conn_list:
    if conn.connection_type == ConnectionType.AZURE_AI_SEARCH:
        conn_id = conn.id
        break

print(conn_id)

# Initialize agent AI search tool and add the search index connection id
ai_search = AzureAISearchTool(index_connection_id=conn_id, index_name=index_name)

# Create agent with AI search tool and process assistant run
with project_client:
    agent = project_client.agents.create_agent(
        model=model,
        name="ai-search-assistant",
        instructions="You are a helpful assistant",
        tools=ai_search.definitions,
        tool_resources=ai_search.resources,
        headers={"x-ms-enable-preview": "true"},
    )
    # [END create_agent_with_azure_ai_search_tool]
    print(f"Created agent, ID: {agent.id}")

    # Create thread for communication
    thread = project_client.agents.create_thread()
    print(f"Created thread, ID: {thread.id}")

    # Create message to thread
    message = project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content="what are the hotels offered by Margie's Travel in Las Vegas?",
    )
    print(f"Created message, ID: {message.id}")

    # Create and process agent run in thread with tools
    run = project_client.agents.create_and_process_run(thread_id=thread.id, assistant_id=agent.id)
    print(f"Run finished with status: {run.status}")

    if run.status == "failed":
        print(f"Run failed: {run.last_error}")

    # Delete the assistant when done
    project_client.agents.delete_agent(agent.id)
    print("Deleted agent")

    # Fetch and log all messages
    messages = project_client.agents.list_messages(thread_id=thread.id)
    print(f"Messages: {messages}")
    print("\n")
    
    # print the assistant response
    print(f"Assistant Response: {messages.data[0].content[0].text.value}")
    print("\n")
    
    #Displaying the URL Citation - the URL citation doesn't work too well as of now! 
    content = messages['data'][0]['content'][0]
    url_citation = content['text']['annotations'][0]['url_citation']['url'] 
    print(url_citation)