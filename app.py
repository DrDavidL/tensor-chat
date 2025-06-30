import streamlit as st
import os
from tensorzero import TensorZeroGateway
from tensorzero.types import ChatInferenceResponse, Text
import requests # New import

st.set_page_config(page_title="Chat with OpenRouter (via TensorZero)", page_icon="💬")
st.title("Chat with OpenRouter (via TensorZero)")

# Retrieve OpenRouter API Key
OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]

# Function to fetch models from OpenRouter
@st.cache_data(ttl=3600) # Cache for an hour
def get_openrouter_models():
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get("https://openrouter.ai/api/v1/models", headers=headers)
        response.raise_for_status() # Raise an exception for HTTP errors
        models_data = response.json()
        # Filter for chat models and extract their IDs
        chat_models = [m['id'] for m in models_data['data'] if 'id' in m and any(keyword in m['id'].lower() for keyword in ['chat', 'gpt', 'llama', 'mistral', 'claude'])]
        return sorted(chat_models)
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching models from OpenRouter: {e}")
        return []

# Function to fetch models from Ollama
@st.cache_data(ttl=3600) # Cache for an hour
def get_ollama_models():
    try:
        response = requests.get("http://localhost:11434/api/tags")
        response.raise_for_status()
        models_data = response.json()
        return sorted([m['name'] for m in models_data['models']])
    except requests.exceptions.RequestException as e:
        st.warning(f"Could not connect to Ollama. Make sure Ollama is running at http://localhost:11434. Error: {e}")
        return []

# Get available OpenRouter models
available_openrouter_models = get_openrouter_models()
default_openrouter_model = "openai/gpt-4o-mini"
if default_openrouter_model not in available_openrouter_models:
    available_openrouter_models.insert(0, default_openrouter_model)

# Add Ollama as an option
model_providers = ["OpenRouter", "Ollama"]
selected_provider = st.sidebar.selectbox("Select Model Provider", model_providers, key="selected_provider")

selected_model_name = ""
if selected_provider == "OpenRouter":
    selected_model_name = st.sidebar.selectbox(
        "Select OpenRouter Model",
        available_openrouter_models,
        index=available_openrouter_models.index(default_openrouter_model) if default_openrouter_model in available_openrouter_models else 0,
        key="selected_openrouter_model"
    )
elif selected_provider == "Ollama":
    available_ollama_models = get_ollama_models()
    if available_ollama_models:
        selected_model_name = st.sidebar.selectbox(
            "Select Ollama Local Model",
            available_ollama_models,
            key="selected_ollama_model"
        )
    else:
        st.sidebar.warning("No Ollama models found. Please ensure Ollama is running and models are downloaded.")
        st.stop() # Stop the app if no Ollama models are available when Ollama is selected

# Ensure the config directory exists (for local development/testing)
os.makedirs("config", exist_ok=True)

# Write the tensorzero.toml content with the selected model
tensorzero_toml_content = ""
if selected_provider == "OpenRouter":
    tensorzero_toml_content = f"""
[functions.chat_app]
type = "chat"

[models.openrouter_model]
routing = ["openrouter_provider"]

[models.openrouter_model.providers.openrouter_provider]
type = "openrouter"
model_name = "{selected_model_name}"

[functions.chat_app.variants.default_variant]
type = "chat_completion"
weight = 1.0
model = "openrouter_model"
"""
elif selected_provider == "Ollama":
    tensorzero_toml_content = f"""
[functions.chat_app]
type = "chat"

[models.ollama_model]
routing = ["ollama_provider"]

[models.ollama_model.providers.ollama_provider]
type = "openai" # Changed from "ollama"
model_name = "{selected_model_name}"
api_base = "http://localhost:11434/v1" # Changed from base_url to api_base

[functions.chat_app.variants.default_variant]
type = "chat_completion"
weight = 1.0
model = "ollama_model"
"""

with open("config/tensorzero.toml", "w") as f:
    f.write(tensorzero_toml_content)

# Initialize TensorZero Gateway
try:
    gateway = TensorZeroGateway.build_embedded(
        clickhouse_url="http://chuser:chpassword@localhost:8123/tensorzero",
        config_file="config/tensorzero.toml",
    )
except Exception as e:
    st.error(f"Error initializing TensorZero Gateway. Make sure ClickHouse is running and OPENROUTER_API_KEY is set in .streamlit/secrets.toml. Error: {e}")
    st.stop()

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "episode_id" not in st.session_state:
    st.session_state.episode_id = None

# System Prompt Configuration
DEFAULT_SYSTEM_PROMPTS = {
    "Default": "You are a helpful AI assistant.",
    "Creative Writer": "You are a creative writer, skilled in crafting engaging stories and poems.",
    "Technical Expert": "You are a highly knowledgeable technical expert, providing precise and accurate information.",
    "Friendly Companion": "You are a friendly and empathetic companion, always ready to listen and offer support."
}

st.sidebar.subheader("System Prompt")
system_prompt_choice = st.sidebar.selectbox(
    "Choose a system prompt preset:",
    list(DEFAULT_SYSTEM_PROMPTS.keys()),
    key="system_prompt_preset"
)

custom_system_prompt = st.sidebar.text_area(
    "Or enter a custom system prompt:",
    value=DEFAULT_SYSTEM_PROMPTS[system_prompt_choice],
    key="custom_system_prompt"
)

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What do you want to talk about?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare messages for TensorZero API call
    messages_for_api = []

    # Create a copy of session messages to modify for API call
    temp_messages = st.session_state.messages.copy()

    # Prepend system prompt to the first user message if it exists
    if custom_system_prompt:
        # Find the first user message
        first_user_message_index = -1
        for i, msg in enumerate(temp_messages):
            if msg["role"] == "user":
                first_user_message_index = i
                break

        if first_user_message_index != -1:
            temp_messages[first_user_message_index]["content"] = \
                f"{custom_system_prompt}\n\n{temp_messages[first_user_message_index]['content']}"
        # else: If there's no user message yet, the system prompt won't be applied.
        # This scenario is unlikely with st.chat_input which always provides a user prompt.

    for message in temp_messages:
        messages_for_api.append({"role": message["role"], "content": message["content"]})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        try:
            # Make inference call to TensorZero
            inference_args = {
                "function_name": "chat_app",
                "input": {
                    "messages": messages_for_api
                }
            }
            if st.session_state.episode_id:
                inference_args["episode_id"] = st.session_state.episode_id

            response: ChatInferenceResponse = gateway.inference(**inference_args)

            # Extract assistant's response
            if response.content and isinstance(response.content[0], Text):
                full_response = response.content[0].text
            else:
                full_response = "Sorry, I couldn't get a response from the model."

            # Update episode_id for future turns
            if response.episode_id and not st.session_state.episode_id:
                st.session_state.episode_id = response.episode_id

        except Exception as e:
            full_response = f"An error occurred: {e}"
            st.error(full_response)

        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
