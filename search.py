import os
import openai
from openai import AzureOpenAI
from datetime import datetime, timezone, timedelta
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

from config import (
    OPENAI_API_TYPE, OPENAI_API_KEY, OPENAI_API_VERSION, OPENAI_API_MODEL,
    AZURE_AI_SEARCH_ENDPOINT, AZURE_AI_SEARCH_KEY, AZURE_AI_SEARCH_INDEX,
    OPENAI_API_MAX_TOKENS, OPENAI_API_TEMPERATURE, OPENAI_API_TOP_P, NO_OF_CONTEXT,AZURE_OPENAI_ENDPOINT
)

openai.api_type = OPENAI_API_TYPE
openai.api_key = OPENAI_API_KEY
openai.api_version = OPENAI_API_VERSION

def get_search_connection():
    credential = AzureKeyCredential(AZURE_AI_SEARCH_KEY)
    client = SearchClient(endpoint=AZURE_AI_SEARCH_ENDPOINT, index_name=AZURE_AI_SEARCH_INDEX, credential=credential)
    return client

def get_text_vector(text):
    try:
        text = text.replace("\n", " ")
        return openai.embeddings.create(input = [text], model="embedding").data[0].embedding
    except:
        pass
def save_embedding_to_search(documents):
    for doc in documents:
        if doc["text"] == '':
            print("Text is Null")
        else:
            text_vector = get_text_vector(doc["text"])
            doc["textVector"] = text_vector
    
    client = get_search_connection()
    client.upload_documents(documents=documents)
    client.close()

def merge_or_upload_documents(documents):
    client = get_search_connection()
    client.merge_or_upload_documents(documents=documents)
    client.close()

def delete_documents_by_request_id(request_id):
    client = get_search_connection()
    thirty_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=30)
    thirty_minutes_ago_iso = thirty_minutes_ago.isoformat()
    results = client.search(filter=f"requestId eq '{request_id}'")
    for result in results:
        document_ids = [{"id": result["id"]}]
        try:
            client.delete_documents(document_ids)
            results = client.search(filter=f"timeStamp lt {thirty_minutes_ago_iso}")
            document_ids = [{"id": result["id"]} for result in results]
            if document_ids:
                client.delete_documents(document_ids)
        except Exception as e:
            pass
    client.close()

def call_large_model(messages, resource):
    client = AzureOpenAI(
            api_key=resource['apiKey'],  
            api_version="2023-05-15",
            azure_endpoint=resource['baseURL']
    )
    response = client.chat.completions.create(
        messages=messages,
        model=OPENAI_API_MODEL,
        max_tokens=OPENAI_API_MAX_TOKENS,
        temperature=OPENAI_API_TEMPERATURE,
        top_p=OPENAI_API_TOP_P
    )
    return response.choices[0].message.content
    

def search_documents(request_id, query):
    query_vector = get_text_vector(query)
    client = get_search_connection()
    try:
        embedding = openai.embeddings.create(input = query, model="embedding").data[0].embedding
    except:
        pass
    vector_query = VectorizedQuery(vector=embedding, k_nearest_neighbors=NO_OF_CONTEXT, fields="textVector", exhaustive=True)
    results = client.search(  
        search_text=query,  
        vector_queries= [vector_query],
        select=["Seitenzahl","Dateiname","text"],
        filter=f"requestId eq '{request_id}'",
        top=NO_OF_CONTEXT
    )
    client.close()
    return results