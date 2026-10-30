import os 
import json
import sys
from promptflow.client import load_flow
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient

load_dotenv()

credential = DefaultAzureCredential()

class PolitenessEvaluator:
    def __init__(self, model_config):
        current_dir = os.path.dirname(__file__)
        prompty_path = os.path.join(current_dir, "politeness.prompty")
        self._flow = load_flow(source=prompty_path, model={"configuration": model_config})

    def __call__(self, *, response: str, **kwargs):
        llm_response = self._flow(response=response)
        try:
            response = json.loads(llm_response)
        except Exception as ex:
            response = llm_response
        return response

def agent_creation_and_completion(query: str):
    project_client = AIProjectClient.from_connection_string(
        credential=DefaultAzureCredential(),
        conn_str=os.getenv("PROJECT_CONNECTION_STRING")
    )

    model=os.getenv("AZURE_OPENAI_DEPLOYMENT")

    agent = project_client.agents.create_agent(
            model=model,
            name="bing-assistant",
            instructions="You are a helpful assistant that is used to assist users with their queries.",
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
            content=query,
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
    
    return messages.data[0].content[0].text.value

def main():
# Initialize Azure AI project and Azure OpenAI conncetion with your environment variables
    azure_ai_project = {
        "subscription_id": os.getenv("AZURE_SUBSCRIPTION_ID"),
        "resource_group_name": os.getenv("AZURE_RESOURCE_GROUP"),
        "project_name": os.getenv("AZURE_PROJECT_NAME"),
    }

    model_config = {
        "type": "AzureOpenAI",
        "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        "azure_deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
    }

    politeness_eval = PolitenessEvaluator(model_config)
    
    response = agent_creation_and_completion(query="can you show me the direction to the nearest restaurant?")

    politeness_score = politeness_eval(response=response)
    print(politeness_score)
    
if __name__ == "__main__":
    main()
