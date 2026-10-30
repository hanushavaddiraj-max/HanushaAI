import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import BingGroundingTool
from dotenv import load_dotenv

load_dotenv()

project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=os.getenv("PROJECT_CONNECTION_STRING")
)

model=os.getenv("MODEL_DEPLOYMENT_NAME")

bing_connection_name = os.getenv("BING_CONNECTION_NAME")

bing_connection = project_client.connections.get(connection_name=bing_connection_name)
conn_id = bing_connection.id

bing = BingGroundingTool(connection_id=conn_id)

with project_client:
    agent = project_client.agents.create_agent(
        model=model,
        name="bing-assistant",
        instructions="You are a helpful assistant",
        tools=bing.definitions,
        headers={"x-ms-enable-preview": "true"},
    )

    print(f"Created agent, ID: {agent.id}")

    # Create thread for communication
    thread = project_client.agents.create_thread()
    print(f"Created thread, ID: {thread.id}")

    # Create message to thread
    message = project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content="whats the weather in London now?",
    )
    print(f"Created message, ID: {message.id}")

    # Create and process agent run in thread with tools
    run = project_client.agents.create_and_process_run(thread_id=thread.id, assistant_id=agent.id)
    print(f"Run finished with status: {run.status}")

    if run.status == "failed":
        print(f"Run failed: {run.last_error}")


    # Fetch and log all messages
    messages = project_client.agents.list_messages(thread_id=thread.id)
    #Displaying the assistant response
    print(messages.data[0].content[0].text.value)
    
    #Displaying the URL Citation
    content = messages['data'][0]['content'][0]['text']['annotations']
    for annotation in content:
     url_citation = annotation['url_citation']['url']
     print(url_citation)
    
    
