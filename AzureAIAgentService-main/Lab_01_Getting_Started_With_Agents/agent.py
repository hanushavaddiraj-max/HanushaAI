import os, time
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import MessageTextContent
from dotenv import load_dotenv

load_dotenv()
# [START create_project_client]
project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=os.getenv("PROJECT_CONNECTION_STRING")
)

model=os.getenv("MODEL_DEPLOYMENT_NAME")


with project_client:

    # [START create_agent]
    agent = project_client.agents.create_agent(  #add get_agent(assistant_id="") for using already created agent
        model=model,
        name="my-assistant",
        instructions="You are helpful assistant",
    )
    # [END create_agent]
    print(f"Created agent, agent ID: {agent.id}")

    # [START create_thread]
    thread = project_client.agents.create_thread()  #add get_thread(thread_id="") for using already created thread
    # [END create_thread]
    print(f"Created thread, thread ID: {thread.id}")

    # [START create_message]
    message = project_client.agents.create_message(thread_id=thread.id, role="user", content="Hello, Tell me something about India")
    # [END create_message]
    print(f"Created message, message ID: {message.id}")

    # [START create_run]
    run = project_client.agents.create_run(thread_id=thread.id, assistant_id=agent.id) #add create_and_process_run for inherent logic implementation

    # Poll the run as long as run status is queued or in progress
    while run.status in ["queued", "in_progress", "requires_action"]:
        # Wait for a second
        time.sleep(1)
        run = project_client.agents.get_run(thread_id=thread.id, run_id=run.id)
        # [END create_run]
        print(f"Run status: {run.status}")


    # [START list_messages]
    messages = project_client.agents.list_messages(thread_id=thread.id)

    #Displaying the message id
    print(messages.data[0].id)
    
    #Displaying the assistant response
    print(messages.data[0].content[0].text.value)

    # [END list_messages]
    print(f"Messages: {messages}")