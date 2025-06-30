# Streamlit Chat App with TensorZero, OpenRouter, and Ollama

This is a Streamlit-based chat application that leverages the TensorZero Gateway for LLM observability, optimization, and routing. It supports interacting with models from OpenRouter (a unified API for various LLMs) and local models served via Ollama.

## Features

*   **Flexible Model Selection:** Choose between OpenRouter and your local Ollama instance as the model provider.
*   **Dynamic Model Listing:**
    *   For OpenRouter, models are fetched dynamically from the OpenRouter API.
    *   For Ollama, local models available on your running Ollama server are listed.
*   **Customizable System Prompts:** Define a system prompt for the AI assistant using pre-defined presets or a custom text entry.
*   **TensorZero Integration:** Utilizes TensorZero Gateway for managing LLM calls, enabling potential future features like A/B testing, prompt engineering, and detailed observability.

## Prerequisites

Before you begin, ensure you have the following installed:

*   **Docker and Docker Compose:** Essential for running ClickHouse (TensorZero's database) and the TensorZero Gateway.
    *   [Install Docker](https://docs.docker.com/get-docker/)
*   **Python 3.x:** The application is built with Python.
    *   [Install Python](https://www.python.org/downloads/)
*   **Ollama (Optional):** If you plan to use local models, you'll need Ollama installed and running.
    *   [Install Ollama](https://ollama.com/download)
    *   Download models (e.g., `ollama pull llama2`).

## Setup Instructions

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/tensor-chat.git # Replace with your actual repo URL
    cd tensor-chat
    ```

2.  **Create a Python Virtual Environment and Install Dependencies:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Configure API Keys:**
    Create a `.streamlit/secrets.toml` file in the root of your project (if it doesn't exist) and add your OpenRouter API key:
    ```toml
    # .streamlit/secrets.toml
    OPENROUTER_API_KEY="sk-or-v1-YOUR_OPENROUTER_API_KEY"
    ```
    You can obtain an OpenRouter API key from [OpenRouter](https://openrouter.ai/keys).

4.  **Start TensorZero Gateway and ClickHouse:**
    The `docker-compose.yml` file sets up ClickHouse (for TensorZero's observability data) and the TensorZero Gateway.
    ```bash
    docker compose up -d
    ```
    **Important Note on ClickHouse Credentials:** For local development, default credentials (`chuser`/`chpassword`) are used. If you plan to deploy ClickHouse in a production or publicly accessible environment, it is crucial to change these default credentials to strong, unique passwords for security reasons.

    This will start the necessary backend services in detached mode.

5.  **Ensure Ollama is Running (if using local models):**
    If you intend to use Ollama models, make sure your Ollama server is running and you have downloaded the desired models (e.g., `ollama pull llama2`). The application will attempt to connect to Ollama at `http://localhost:11434`.

## Running the Application

Once all prerequisites are met and services are running, you can start the Streamlit application:

```bash
streamlit run app.py
```

Open your web browser and navigate to the address provided by Streamlit (usually `http://localhost:8501`).

## TensorZero and Evaluations

TensorZero Gateway plays a crucial role in this application by acting as an intermediary for all LLM calls. This setup allows for:

*   **Centralized Configuration:** Manage model routing and variants through `config/tensorzero.toml`.
*   **Observability:** TensorZero logs all inference calls to ClickHouse, providing valuable data for monitoring model performance and usage.
*   **Future Evaluations:** The architecture is set up to easily integrate advanced features like A/B testing different models or prompts, and conducting automated evaluations of model responses, all managed through TensorZero.

Feel free to explore the `app.py` and `config/tensorzero.toml` files to understand how the different components are integrated.

![alt text](<CleanShot 2025-06-29 at 21.45.10@2x.png>)
