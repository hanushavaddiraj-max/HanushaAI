#pip install azure-ai-evaluation

import os 
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from azure.ai.evaluation import GroundednessProEvaluator, GroundednessEvaluator
from azure.ai.evaluation import CoherenceEvaluator, FluencyEvaluator, SimilarityEvaluator
import json

load_dotenv()


credential = DefaultAzureCredential()

# Initialize Azure AI project and Azure OpenAI conncetion with your environment variables
azure_ai_project = {
    "subscription_id": os.getenv("AZURE_SUBSCRIPTION_ID"),
    "resource_group_name": os.getenv("AZURE_RESOURCE_GROUP"),
    "project_name": os.getenv("AZURE_PROJECT_NAME"),
}

model_config = {
    "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
    "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
    "azure_deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
}


# Initialzing Groundedness and Groundedness Pro evaluators
groundedness_eval = GroundednessEvaluator(model_config)
groundedness_pro_eval = GroundednessProEvaluator(azure_ai_project=azure_ai_project, credential=credential)

query_response = dict(
    query="Which tent is the most waterproof?",
    context="The Alpine Explorer Tent is the second most water-proof of all tents available.",
    response="The Alpine Explorer Tent is the most waterproof."
)

# Running Groundedness Evaluator on a query and response pair
groundedness_score = groundedness_eval(
    **query_response
)
json.dumps(groundedness_score)

print(groundedness_score['groundedness_reason'])

groundedness_pro_score = groundedness_pro_eval(
    **query_response
)
print(groundedness_pro_score)

#Running Coherence check and evaluation
coherence_score = CoherenceEvaluator(model_config)(**query_response)
print(coherence_score)

#Running fluency check and evaluation
fluency_score = FluencyEvaluator(model_config)(**query_response)
print(fluency_score)


