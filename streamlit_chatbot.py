import json
import os
from dotenv import load_dotenv
from langchain.agents import initialize_agent, Tool
from langchain_openai import ChatOpenAI
from openshift import (
    get_applications,
    get_pods_and_status_health_for_application,
    restart_application,
    upgrade_application,
    scale_application_pods,
    get_application_logs,
    get_deployment_configs,
    get_application_telemetry_data,
    check_cluster_nodes_health,
    check_critical_components_health,
    check_resource_utilization_health,
)
import streamlit as st
import urllib3
import warnings

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")

# Load environment variables from .env
load_dotenv()

# Get AI Together API key from environment variable
ait_api_key = os.getenv("AIT_API_KEY")
if not ait_api_key:
    raise ValueError("AI Together API key is missing. Please set it in the .env file.")

# Define tools for the agent
tools = [
    Tool(
        name="get_applications",
        func=get_applications,
        description="List all application names (deployments) in the 'mindovermachinestech-dev' namespace.",
    ),
    Tool(
        name="get_pods_and_status_health_for_application",
        func=get_pods_and_status_health_for_application,
        description="Get all pods for a specific application along with pod status in the 'mindovermachinestech-dev' namespace.",
    ),
    Tool(
        name="restart_application",
        func=restart_application,
        description="Restart a specific application in the 'mindovermachinestech-dev' namespace. Input should be the application name.",
    ),
    Tool(
        name="upgrade_application",
        func=upgrade_application,
        description="Upgrade a specific application to a new container image in the 'mindovermachinestech-dev' namespace. Input should include the application name and the new image.",
    ),
    Tool(
        name="scale_application_pods",
        func=scale_application_pods,
        description="Scale the number of pods for a specific application in the 'mindovermachinestech-dev' namespace. Input should include the application name and the desired number of replicas.",
    ),
    Tool(
        name="get_application_logs",
        func=get_application_logs,
        description="Fetch logs for a specific application in the 'mindovermachinestech-dev' namespace.",
    ),
    Tool(
        name="get_deployment_configs",
        func=get_deployment_configs,
        description="Fetch deployment configurations for a specific application in the 'mindovermachinestech-dev' namespace.",
    ),
    Tool(
        name="get_application_telemetry_data",
        func=get_application_telemetry_data,
        description="Fetch telemetry and monitoring data for a specific application in the 'mindovermachinestech-dev' namespace.",
    ),
    Tool(
        name="check_critical_components_health",
        func=check_critical_components_health,
        description="Fetch critical components health and monitoring data for the OpenShift cluster in the 'mindovermachinestech-dev' namespace.",
    ),
    Tool(
        name="check_resource_utilization_health",
        func=check_resource_utilization_health,
        description="Fetch resource utilization for OpenShift cluster components as part of health checks in the 'mindovermachinestech-dev' namespace.",
    ),
]

# Initialize LLM using Together AI
llm = ChatOpenAI(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    openai_api_key=ait_api_key,
    base_url="https://api.together.xyz/v1",
)

# System Prompt
SYSTEM_PROMPT = """
You are an OpenShift Operations Assistant designed to help users manage applications and resources in the 'mindovermachinestech-dev' namespace.
Provide information along with sources.
"""

# Initialize the agent with the system prompt
agent = initialize_agent(
    tools,
    llm,
    agent="zero-shot-react-description",
    verbose=True,
    system_prompt=SYSTEM_PROMPT,
)

# Parse user input using LLM to extract parameters for the tools
def parse_user_input(user_input):
    try:
        # Define the prompt for the LLM
        prompt = f"""
        You are an assistant designed to extract structured information from user commands related to OpenShift operations.
        Your task is to analyze the user input and extract the following fields if they are present:
        - app_name: The name of the application (e.g., "rule-engine", "my-app").
        - tail_lines: The number of log lines to fetch (e.g., "50", "100").
        - replicas: The number of replicas for scaling (e.g., "2", "5").
        - new_image: The new container image for upgrading (e.g., "nginx:latest", "my-image:v2").

        IMPORTANT: Return ONLY the JSON object as plain text, without any additional explanation or formatting tags.
        Ensure the JSON object contains only the extracted fields and their values.

        User Input: "{user_input}"

        Extracted Information (in JSON format):
        """

        # Use the LLM to generate the response
        llm_response = llm.invoke(prompt)
        response_content = llm_response.content if hasattr(llm_response, 'content') else llm_response.text

        # Safely parse the JSON response
        extracted_info = json.loads(response_content.strip())
        return extracted_info
    except Exception as e:
        st.error(f"Error parsing user input: {str(e)}")
        return {}

# Streamlit App
def main():
    st.title("OpenShift Operations Chatbot")

    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("How can I assist you today?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Parse user input
        parsed_input = parse_user_input(prompt)

        # Pass the parsed input to the agent
        try:
            response = agent.run(input=prompt)
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": error_message})
            with st.chat_message("assistant"):
                st.markdown(error_message)

# Run the Streamlit app
if __name__ == "__main__":
    main()