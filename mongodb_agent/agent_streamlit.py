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
import streamlit as st
from pymongo import MongoClient
import pandas as pd
from langchain_ollama import OllamaLLM
import ast

# MongoDB connection
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["stock_db"]
collection = db["predictions"]

# Initialize the Ollama LLM
llm = OllamaLLM(
    model="llama3.2:latest",
    temperature=0.1,
    base_url="http://localhost:11434"
)

st.set_page_config(page_title="MongoDB Natural Language Agent", layout="wide")
st.title("🤖 MongoDB Natural Language Agent ")

# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Input area with Enter button
with st.form(key="query_form", clear_on_submit=True):
    user_query = st.text_input("Your query:", "")
    submit = st.form_submit_button("Enter")

if submit and user_query:
    # Add user query to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_query})

    with st.spinner("Thinking..."):
        # Prompt LLM to generate a MongoDB aggregation pipeline
        prompt = (
            f"Convert the following natural language request into a valid MongoDB aggregation pipeline "
            f"for the 'predictions' collection. Return ONLY a valid Python list of pipeline stages. "
            f"Do not include any additional text, explanations, or code formatting. "
            f"Request: {user_query}"
        )
        pipeline_str = llm(prompt)
        # Add LLM pipeline to chat history
        st.session_state.chat_history.append({"role": "llm", "content": f"Pipeline: {pipeline_str}"})

        # Clean and validate the pipeline string
        pipeline_str = pipeline_str.strip().replace("```python", "").replace("```", "").strip()
        
        # Add function to clean up string literals
        def clean_string(s):
            # Remove any trailing commas that might cause issues
            s = s.rstrip(',')
            # Balance quotes - remove any unclosed quotes
            if s.count('"') % 2 != 0:
                if s.startswith('"'):
                    s = s + '"'
                else:
                    s = '"' + s
            return s
        
        # Clean the entire string
        pipeline_str = clean_string(pipeline_str)
        
        # Try to safely evaluate the pipeline string with better validation
        try:
            # Try parsing the string first to catch any syntax errors
            parsed = ast.parse(pipeline_str, mode='eval')
            
            # Now evaluate the string
            pipeline = ast.literal_eval(pipeline_str)
            
            # If it's not a list, try to convert it
            if not isinstance(pipeline, list):
                # If it's a string, try to evaluate it as a list
                if isinstance(pipeline, str):
                    pipeline = ast.literal_eval(pipeline)
                # If it's still not a list, raise error
                if not isinstance(pipeline, list):
                    raise ValueError("Pipeline is not a list. Please ensure the response is a valid Python list.")
            
            # Convert any string stages to dictionaries
            converted_pipeline = []
            for i, stage in enumerate(pipeline):
                if isinstance(stage, str):
                    # Clean the stage string
                    stage = clean_string(stage)
                    # Try to convert string to dict
                    try:
                        stage_dict = ast.literal_eval(stage)
                        if not isinstance(stage_dict, dict):
                            raise ValueError(f"Pipeline stage {i+1} could not be converted to a dictionary")
                        converted_pipeline.append(stage_dict)
                    except:
                        # Try wrapping in braces if it looks like a stage
                        if stage.startswith('{') and stage.endswith('}'):
                            stage_dict = ast.literal_eval(stage)
                            converted_pipeline.append(stage_dict)
                        else:
                            stage_dict = ast.literal_eval("{" + stage + "}")
                            converted_pipeline.append(stage_dict)
                elif isinstance(stage, dict):
                    converted_pipeline.append(stage)
                else:
                    raise ValueError(f"Pipeline stage {i+1} is not a dictionary: {stage}")
            
            pipeline = converted_pipeline
        except Exception as e:
            error_msg = f"Could not parse aggregation pipeline: {e}"
            st.session_state.chat_history.append({"role": "error", "content": error_msg})
            st.error(error_msg)
            st.stop()

        # Run the aggregation pipeline
        try:
            result = list(collection.aggregate(pipeline))
            if result:
                df = pd.DataFrame(result)
                st.session_state.chat_history.append({"role": "llm", "content": f"Result:\n{df.to_markdown(index=False)}"})
            else:
                st.session_state.chat_history.append({"role": "llm", "content": "No results found for this query."})
        except Exception as agg_error:
            error_msg = f"Error running aggregation pipeline: {agg_error}"
            st.session_state.chat_history.append({"role": "error", "content": error_msg})
            st.error(error_msg)
# Display chat history
st.markdown("### Conversation")
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    elif msg["role"] == "llm":
        if msg["content"].startswith("Result:"):
            st.markdown(f"**Agent:**\n\n{msg['content'][7:]}")
        else:
            st.markdown(f"**Agent:** {msg['content']}")
    elif msg["role"] == "error":
        st.error(msg["content"])
