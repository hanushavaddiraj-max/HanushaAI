import os
import jsonref
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import OpenApiTool, OpenApiAnonymousAuthDetails
from dotenv import load_dotenv

load_dotenv()
project_connection_string = os.getenv("PROJECT_CONNECTION_STRING")
model=os.getenv("MODEL_DEPLOYMENT_NAME")

project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=project_connection_string,
)
# [START create_agent_with_openapi]

with open("./weather_openapi.json", "r") as f:
    openapi_spec = jsonref.loads(f.read())

# Create Auth object for the OpenApiTool 
auth = OpenApiAnonymousAuthDetails()

# Initialize agent OpenApi tool using the read in OpenAPI spec
openapi = OpenApiTool(
    name="get_weather", spec=openapi_spec, description="Retrieve weather information for a location", auth=auth
)

# Create agent with OpenApi tool and process assistant run
with project_client:
    agent = project_client.agents.create_agent(
        model=model,
        name="openapi-function-assistant",
        instructions="You are a helpful assistant",
        tools=openapi.definitions,
    )

    # [END create_agent_with_openapi]

    print(f"Created agent, ID: {agent.id}")

    # Create thread for communication
    thread = project_client.agents.create_thread()
    print(f"Created thread, ID: {thread.id}")

    # Create message to thread
    message = project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content="What's the weather and humidity in Seattle?",
    )
    print(f"Created message, ID: {message.id}")

    # Create and process agent run in thread with tools
    run = project_client.agents.create_and_process_run(thread_id=thread.id, assistant_id=agent.id)
    print(f"Run finished with status: {run.status}")

    if run.status == "failed":
        print(f"Run failed: {run.last_error}")

    

    # Fetch and log all messages
    messages = project_client.agents.list_messages(thread_id=thread.id)
    print(f"Messages: {messages}")
    print("\n")
    
    # print the assistant response
    print(f"Assistant Response: {messages.data[0].content[0].text.value}")