import os
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import CodeInterpreterTool, MessageAttachment
from azure.ai.projects.models import FilePurpose, MessageRole
from azure.identity import DefaultAzureCredential
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

model = os.getenv("MODEL_DEPLOYMENT_NAME")
project_connection_string = os.getenv("PROJECT_CONNECTION_STRING")

project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(), 
    conn_str=project_connection_string
)



with project_client:

    # Upload a file and wait for it to be processed
    file = project_client.agents.upload_file_and_poll(
        file_path="electronics_products.csv", purpose=FilePurpose.AGENTS
    )
    print(f"Uploaded file, file ID: {file.id}")

    # [START create_agent_and_message_with_code_interpreter_file_attachment]
    # Notice that CodeInterpreter must be enabled in the agent creation,
    # otherwise the agent will not be able to see the file attachment for code interpretation
    agent = project_client.agents.create_agent(
        model=model,
        name="code-interpreter-assistant",
        instructions="You are helpful assistant meant to answer user query by analysing the file provided to you",
        tools=CodeInterpreterTool().definitions,
    )
    print(f"Created agent, agent ID: {agent.id}")

    thread = project_client.agents.create_thread()
    print(f"Created thread, thread ID: {thread.id}")

    # Create an attachment
    attachment = MessageAttachment(file_id=file.id, tools=CodeInterpreterTool().definitions)

    # Create a message
    message = project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content="Could you please create a column chart with products on the x-axis and their respective prices on the y-axis?",
        attachments=[attachment],
    )
    # [END create_agent_and_message_with_code_interpreter_file_attachment]
    print(f"Created message, message ID: {message.id}")

    run = project_client.agents.create_and_process_run(thread_id=thread.id, assistant_id=agent.id)
    print(f"Run finished with status: {run.status}")

    if run.status == "failed":
        # Check if you got "Rate limit is exceeded.", then you want to get more quota
        print(f"Run failed: {run.last_error}")


    messages = project_client.agents.list_messages(thread_id=thread.id)
    print(f"Messages: {messages}")

    last_msg = messages.get_last_text_message_by_role(MessageRole.AGENT)
    if last_msg:
        print(f"Last Message: {last_msg.text.value}")

    for image_content in messages.image_contents:
        print(f"Image File ID: {image_content.image_file.file_id}")
        file_name = f"{image_content.image_file.file_id}_image_file.png"
        project_client.agents.save_file(file_id=image_content.image_file.file_id, file_name=file_name)
        print(f"Saved image file to: {Path.cwd() / file_name}")

    

    