from typing import Any, Callable, Set
from functions import user_functions
import os, time, json
from azure.ai.projects import AIProjectClient
from azure.ai.projects.telemetry import trace_function
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import FunctionTool, RequiredFunctionToolCall, SubmitToolOutputsAction, ToolOutput
from opentelemetry import trace
from azure.monitor.opentelemetry import configure_azure_monitor
from dotenv import load_dotenv
import logging

load_dotenv()
project_connection_string=os.getenv("PROJECT_CONNECTION_STRING")
model = os.getenv("MODEL_DEPLOYMENT_NAME")

project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=project_connection_string
)

# Enable Azure Monitor tracing
application_insights_connection_string = project_client.telemetry.get_connection_string()
if not application_insights_connection_string:
    print("Application Insights was not enabled for this project.")
    print("Enable it via the 'Tracing' tab in your AI Foundry project page.")
    exit()
configure_azure_monitor(connection_string=application_insights_connection_string)

scenario = os.path.basename(__file__)
tracer = trace.get_tracer(__name__)


functions = FunctionTool(functions=user_functions)

with tracer.start_as_current_span(scenario):
    with project_client:
        # Create an agent and run user's request with function calls
        agent = project_client.agents.create_agent(
            model=model,
            name="my-function-tracing-assistant",
            instructions="You are a helpful assistant",
            tools=functions.definitions,
        )
        print(f"Created agent, ID: {agent.id}")

        thread = project_client.agents.create_thread()
        print(f"Created thread, ID: {thread.id}")
        
        user_query = "What is the weather in Seattle and email id for user1?"
        
        message = project_client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content=user_query,
        )
        print(f"Created message, ID: {message.id}")

        run = project_client.agents.create_run(thread_id=thread.id, assistant_id=agent.id)
        print(f"Created run, ID: {run.id}")

        while run.status in ["queued", "in_progress", "requires_action"]:
            time.sleep(1)
            run = project_client.agents.get_run(thread_id=thread.id, run_id=run.id)

            if run.status == "requires_action" and isinstance(run.required_action, SubmitToolOutputsAction):
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                if not tool_calls:
                    print("No tool calls provided - cancelling run")
                    project_client.agents.cancel_run(thread_id=thread.id, run_id=run.id)
                    break

                tool_outputs = []
                for tool_call in tool_calls:
                    if isinstance(tool_call, RequiredFunctionToolCall):
                        try:
                            output = functions.execute(tool_call)
                            tool_outputs.append(
                                ToolOutput(
                                    tool_call_id=tool_call.id,
                                    output=output,
                                )
                            )
                        except Exception as e:
                            print(f"Error executing tool_call {tool_call.id}: {e}")

                print(f"Tool outputs: {tool_outputs}")
                if tool_outputs:
                    project_client.agents.submit_tool_outputs_to_run(
                        thread_id=thread.id, run_id=run.id, tool_outputs=tool_outputs
                    )

            print(f"Current run status: {run.status}")

        print(f"Run completed with status: {run.status}")
        
         # Fetch and log all messages
        messages = project_client.agents.list_messages(thread_id=thread.id)
        ai_output = messages.data[0].content[0].text.value
        print(ai_output)
        
        if run.usage:
            prompt_tokens = run.usage.prompt_tokens
            completion_tokens = run.usage.completion_tokens
            total_tokens = prompt_tokens + completion_tokens
            with tracer.start_as_current_span("Token Usage") as span:
                span.set_attribute("user input", user_query )
                span.set_attribute("ai_output", ai_output)
                span.set_attribute("ai.prompt_tokens", prompt_tokens)
                span.set_attribute("ai.completion_tokens", completion_tokens)
                span.set_attribute("ai.total_tokens", total_tokens)
            logging.info(f"Token Usage - Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}")
            print(f"Token Usage - Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}")
            print("\n")
            
        # Delete the agent when done
        project_client.agents.delete_agent(agent.id)
        print("Deleted agent")

       