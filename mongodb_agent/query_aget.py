import os
import ssl
import urllib3
import warnings

# Set environment variables to disable SSL verification and telemetry before any other imports
os.environ['PYTHONHTTPSVERIFY'] = '0'  # Disables Python's HTTPS certificate verification
os.environ['CURL_CA_BUNDLE'] = ''      # Unsets CURL CA bundle to avoid SSL errors
os.environ['REQUESTS_CA_BUNDLE'] = ''  # Unsets Requests CA bundle for SSL

# Disable various telemetry and analytics features for LangChain and related libraries
os.environ['LANGCHAIN_TRACING_V2'] = 'false'
os.environ['LANGCHAIN_TELEMETRY'] = 'false'
os.environ['LANGSMITH_TRACING'] = 'false'
os.environ['LANGCHAIN_ANALYTICS'] = 'false'
os.environ['LANGCHAIN_CALLBACKS_MANAGER'] = 'false'
os.environ['LANGCHAIN_VERBOSE'] = 'false'
os.environ['LANGCHAIN_DEBUG'] = 'false'

# Suppress all warnings, including those related to telemetry and SSL
warnings.filterwarnings("ignore")

# Remove SSL_CERT_FILE from environment if it exists, to avoid SSL issues
if 'SSL_CERT_FILE' in os.environ:
    del os.environ['SSL_CERT_FILE']

# Disable SSL warnings from urllib3 (commonly used by requests and other HTTP libraries)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set the default SSL context to not verify certificates (insecure, but useful for local dev)
ssl._create_default_https_context = ssl._create_unverified_context
from langchain_ollama.llms import OllamaLLM  # Import Ollama LLM integration
# from langchain_core.prompts import ChatPromptTemplate  # Import ChatPromptTemplate for prompt handling
from langchain_ollama import OllamaEmbeddings  # Import Ollama embeddings for vectorization         # Import Chroma vector store
from langchain_core.documents import Document  # Import Document class for storing text and metadata
import pandas as pd                            # Import pandas for data manipulation
from langchain_community.document_loaders import PyPDFLoader  # Import PDF loader from langchain_community
from langchain_community.document_loaders import TextLoader
from langchain_core.tools import tool
## MongoDB agent toolkit is not available in langchain_community. We'll use pymongo directly.
from pymongo import MongoClient
from dotenv import load_dotenv, find_dotenv
import os
from pymongo import MongoClient

# Example for MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["stock_db"]
collection = db["predictions"]

## If you want to use LangChain with MongoDB, you may need to adapt the agent setup, as create_sql_agent is for SQL databases.
## For demonstration, the rest of the code is left as-is, but you should use a MongoDB-compatible agent/toolkit for production.

# Initialize the Ollama LLM with the model name and explicit base URL for the local Ollama server
model = OllamaLLM(
    # model="llama3.2",
    model="llama3.2:latest",
    temperature=0.1,  # Set the temperature for response variability
    base_url="http://localhost:11434"  # Ollama server endpoint
)


# If you want embeddings for retrieval tasks
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",                  # Specify the embedding model
    base_url="http://localhost:11434"          # Set the Ollama server URL
)


# Interactive question/answer system using pymongo and LLM
if __name__ == "__main__":
    print("--- MongoDB Query Agent Ready ---")
    print("You can now ask questions about your MongoDB database in natural language.")
    print("Type 'exit' or 'quit' to stop.")

    while True:
        user_query = input("\nYour query: ")
        if user_query.lower() in ["exit", "quit"]:
            print("Exiting agent. Goodbye!")
            break
        try:
            # Ask the LLM to generate a MongoDB aggregation pipeline for the user's request
            prompt = (
                "You are a MongoDB expert. "
                "Given the following user request, generate ONLY a valid MongoDB aggregation pipeline as a Python list of dicts. "
                "Do not include any explanation, markdown, code block markers, or extra text. Output ONLY the Python list.\n"
                f"User request: {user_query}\n"
                "Collection name: predictions\n"
                "Return only the aggregation pipeline as a Python list."
            )
            pipeline_code = model.invoke(prompt)

            import ast
            try:
                pipeline = ast.literal_eval(pipeline_code)
            except Exception as e:
                # Try to extract the first list from the output using regex as a fallback
                import re
                match = re.search(r'(\[.*?\])', pipeline_code, re.DOTALL)
                if match:
                    snippet = match.group(1)
                    try:
                        pipeline = ast.literal_eval(snippet)
                    except Exception as e2:
                        print(f"Could not parse aggregation pipeline: {e2}")
                        continue
                else:
                    print("No valid Python list found in LLM output. Please rephrase your request.")
                    continue

            # Run the aggregation pipeline using PyMongo
            try:
                result = list(collection.aggregate(pipeline))
                # Display only the final answer (first value in result, if any)
                if result:
                    # Try to print the first non-_id value in the result dict
                    answer = None
                    for k, v in result[0].items():
                        if k != '_id':
                            answer = v
                            break
                    if answer is not None:
                        print(f"\n{answer}")
                    else:
                        print("\nNo answer found in aggregation result.")
                else:
                    print("\nAggregation returned no results.")
            except Exception as agg_error:
                print(f"\nError running aggregation pipeline: {agg_error}")
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Please check the query, your database schema, or the LLM configuration.")
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Please check the query, your database schema, or the LLM configuration.")