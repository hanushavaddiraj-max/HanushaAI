from azure.cosmos import CosmosClient, PartitionKey, exceptions
import os
from dotenv import load_dotenv
from openai import AzureOpenAI

def return_results_from_db(user_query):
    
    load_dotenv()

    container_name = os.getenv("CONTAINER_NAME")
    database_name = os.getenv("DATABASE_NAME")
    cosmosdb_connection_string = os.getenv("COSMOSDB_CONNECTION_STRING")
    openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    openai_key = os.getenv("AZURE_OPENAI_KEY")
    embedding_engine = os.getenv("EMBEDDING_EMGINE")


    cosmos_client = CosmosClient.from_connection_string(cosmosdb_connection_string)
    database = cosmos_client.get_database_client(database=database_name)
    container = database.get_container_client(container=container_name)

    openai_client = AzureOpenAI(
        azure_endpoint = openai_endpoint, 
        api_key=openai_key,  
        api_version="2024-02-15-preview"
    )
    
    embeddings_response = openai_client.embeddings.create(
        input=user_query,
        model="text-embedding-ada-002"
    )
    
    embeddings_dict =  embeddings_response.model_dump()
    embeddings_array = embeddings_dict['data'][0]['embedding']
    
    queryText = f""" SELECT TOP 5 c.name, c.description, c.similar_words, c.url, VectorDistance(c.vector, {embeddings_array}) AS SimilarityScore
    FROM c
    ORDER BY VectorDistance(c.vector, {embeddings_array})"""
    query_results = container.query_items(
        query=queryText,
        enable_cross_partition_query=True
    )
    
    images=[]

    for item in query_results:
        print(item)
        images.append(item)
        
    return images
    
    



