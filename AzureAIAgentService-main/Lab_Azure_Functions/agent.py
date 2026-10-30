import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

project_connection_string = os.getenv("PROJECT_CONNECTION_STRING")
model=os.getenv("MODEL_DEPLOYMENT_NAME")
storage_connection_string = os.getenv("STORAGE_CONNECTION_queueServiceUri")
input_queue_name = os.getenv("INPUT_QUEUE_NAME")
output_queue_name = os.getenv("OUTPUT_QUEUE_NAME")

project_client = AIProjectClient.from_connection_string(
        credential=DefaultAzureCredential(),
        conn_str=project_connection_string
    )



agent = project_client.agents.create_agent(
        model=model,
        name="azure-function-agent",
        instructions="You are a helpful support agent. Answer the user's questions to the best of your ability.",
        headers={"x-ms-enable-preview": "true"},
        tools=[
            {
                "type": "azure_function",
                "azure_function": {
                    "function": {
                        "name": "GreetingByBatman",
                        "description": "Deliver a Greeting to the user in Batman's style.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "the name of the user or the name of the person to which the greeting is to be delivered."},
                            },
                            "required": ["name"]
                        }
                    },
                    "input_binding": {
                        "type": "storage_queue",
                        "storage_queue": {
                            "queue_service_uri": storage_connection_string,
                            "queue_name": input_queue_name
                        }
                    },
                    "output_binding": {
                        "type": "storage_queue",
                        "storage_queue": {
                            "queue_service_uri": storage_connection_string,
                            "queue_name": output_queue_name
                        }
                    }
                }
            }
        ],
    )

thread = project_client.agents.create_thread()

message = project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content="deliver a greeting by batman to Kuljot",
)
print(f"Created message, ID: {message.id}")

# Create and process agent run in thread with azure function supplied as a tool
run = project_client.agents.create_and_process_run(thread_id=thread.id, assistant_id=agent.id)
print(f"Run finished with status: {run.status}")

if run.status == "failed":
        print(f"Run failed: {run.last_error}")


# Fetch and log all messages
messages = project_client.agents.list_messages(thread_id=thread.id)
#Displaying the assistant response
print(messages.data[0].content[0].text.value)
    