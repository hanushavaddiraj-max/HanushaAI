""" Azure AI Agent Service MCP Server"""

import os
import sys
import logging
import asyncio
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP, Context
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import MessageRole, Agent
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import Agent
import time

load_dotenv()

# initialize MCP and server
mcp = FastMCP(
    "azure-ai-foundry-mcp",
    description="Azure AI Foundry MCP Server",
    version="0.1.0",
)

# defining helper functions
def create_client():
    conn_str = os.getenv("PROJECT_CONNECTION_STRING")
    parts = conn_str.split(";")
    if len(parts) != 4:
        raise ValueError("Invalid connection string format. Expected format: 'endpoint;subscription_id;resource_group_name;project_name'")

    endpoint, subscription_id, resource_group_name, project_name = parts
    
    credential = DefaultAzureCredential()
    project_client = AIProjectClient(
        credential=credential,
        endpoint=endpoint,
        subscription_id=subscription_id,
        resource_group_name=resource_group_name,
        project_name=project_name,
    )
   
    return project_client

def query_agent_with_agent_id(agent_id, query: str) -> str:
 
    try:
        ai_client = create_client()
        
        thread = ai_client.agents.create_thread()
        

        
        message = ai_client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content=query
        )
       

      
        run = ai_client.agents.create_run(
            thread_id=thread.id,
            agent_id=agent_id
        )
        

        while run.status in ["queued", "in_progress", "requires_action"]:
            
            time.sleep(1)
            run = ai_client.agents.get_run(thread_id=thread.id, run_id=run.id)

        if run.status == "failed":
            error_msg = f"Agent run failed: {run.last_error}"
           
            return f"Error: {error_msg}"

        
        messages = ai_client.agents.list_messages(thread_id=thread.id)
       

        return messages.data[0].content[0].text.value

    except Exception as e:
        
        return f"Error querying agent: {str(e)}"

# Creating MCP tools
@mcp.tool()
def list_agents() -> str:
   
    try:
        ai_client = create_client()
        agents = ai_client.agents.list_agents()
        
        if not agents or not agents.data:
            return "No agents found in Azure AI Agent Service."

        result = "## Available Azure AI Agents \n\n"
        for agent in agents.data:
            result += f"- **{agent.name}**: `{agent.id}`\n"

        
        return result

    except Exception as e:
        
        return f"Error listing agents: {str(e)}"

@mcp.tool()
def query_agent(agent_name: str, query: str) -> str:
    
    try:
        ai_client = create_client()
        agent_id = None
        agents = ai_client.agents.list_agents()
      
        if not agents or not agents.data:
            return "No agents found in Azure AI Agent Service."
        for agent in agents.data:

            if agent.name == agent_name:
                agent_id = agent.id
                
                break

        if not agent_id:
            return f"Agent with name {agent_name} not found."

        response = query_agent_with_agent_id(agent_id, query)
        
        return response

    except Exception as e:
        return f"Error querying agent: {str(e)}"

if __name__ == "__main__":
   
    mcp.run()