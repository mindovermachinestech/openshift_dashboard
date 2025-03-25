import json

from langchain.agents import initialize_agent, Tool
from langchain_openai import ChatOpenAI
from kubernetes import client, config
from dotenv import load_dotenv
import os
import warnings
import urllib3
from openshift import (
    get_openshift_tool
)
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
        name="get_openshift_tool",
        func=get_openshift_tool,
        description="only tool to handle all actions in  'mindovermachinestech-dev' namespace. "
    )
]

# Initialize LLM using Together AI
#ait_api_key = "YOUR_TOGETHER_AI_API_KEY"  # Replace with your actual Together AI API key
llm = ChatOpenAI(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",  # Specify the model you want to use
    openai_api_key=ait_api_key,
    base_url="https://api.together.xyz/v1",
)

# Initialize the agent
# System Prompt
SYSTEM_PROMPT = """
You are an OpenShift Operations Assistant designed to help users manage applications and resources in the 'mindovermachinestech-dev' namespace. 
Your responses should always be clear, concise, and professional.

When providing information:
- Use simple language to explain technical details.
- Format lists or structured data neatly for readability.
- Provide actionable insights where applicable.
- provide output in bullet points if possible

When encountering errors:
- Acknowledge the issue politely.
- Explain what went wrong in non-technical terms.
- Suggest possible next steps or solutions if available.

When performing actions (e.g., scaling pods, restarting apps):
- Confirm the action was successful with a positive message.
- Include relevant details about the outcome.
"""
# Initialize the agent with the system prompt
agent = initialize_agent(
    tools,
    llm,
    agent="zero-shot-react-description",
    verbose=True
)

def parse_user_input(user_input):
    """
    Parse user input using LLM to extract parameters for the tools.
    Fields to extract: app_name, tail_lines, replicas, new_image
    """
    try:
        # Define the prompt for the LLM
        prompt = f"""
        You are an assistant designed to extract structured information from user commands related to OpenShift operations.
        Your task is to analyze the user input and extract the following fields if they are present:
        - app_name: The name of the application (e.g., "rule-engine", "my-app").
        - tail_lines: The number of log lines to fetch (e.g., "50", "100").
        - replicas: The number of replicas for scaling (e.g., "2", "5").
        - new_image: The new container image for upgrading (e.g., "nginx:latest", "my-image:v2").
        - container_image: The container image for deploying (e.g , "quay.io/mindovermachinestech/business-rule-processor:latest").
        
        Also Your task is to analyze the user input identify the tool name to invoke based on user input, tool name must match with any one of below, should not return any other tool name :
        get_applications
        get_pods_and_status_health_for_application
        restart_application
        upgrade_application
        scale_application_pods
        get_application_logs
        get_deployment_configs
        get_application_telemetry_data
        check_cluster_nodes_health
        check_critical_components_health
        check_resource_utilization_health
        deploy_new_application

        The user input may use synonyms or different phrasing. For example:
        - "get logs for rule-engine" -> app_name = "rule-engine"
        - "fetch last 50 lines of logs for my-app" -> app_name = "my-app", tail_lines = 50
        - "scale my-app to 3 pods" -> app_name = "my-app", replicas = 3
        - "update my-app to use nginx:latest" -> app_name = "my-app", new_image = "nginx:latest"
        
        The user input may use synonyms or different tool. For example:
        - "get application details" -> tool_name = "get_applications"
        - "increase number of instances of application to 10" -> tool_name = "scale_application_pods"
        

        IMPORTANT: Return ONLY the JSON object as plain text, without any additional explanation or formatting tags.
        Ensure the JSON object contains only the extracted fields and their values.

        User Input: "{user_input}"

        Extracted Information (in JSON format):
        """

        #print(prompt)
        # Use the LLM to generate the response
        llm_response = llm.invoke(prompt)
        # Extract the raw content from the AIMessage object
        if hasattr(llm_response, 'content'):
            response_content = llm_response.content
        elif hasattr(llm_response, 'text'):
            response_content = llm_response.text
        else:
            raise ValueError("Unsupported response format from LLM.")

        print(f"**** response content *** {response_content.strip()}")
        print(f"**** response content *** {type(response_content)}")

        # Parse the LLM's response into a dictionary
        #extracted_info = eval(response_content.strip())  # Safely parse the JSON-like output
        return response_content
    except Exception as e:
        print(f"Error parsing user input: {str(e)}")
        return {}

# Run the chatbot
print("Welcome to the OpenShift Operations Chatbot!")
while True:
    user_input = input("Enter your command (or type 'exit' to quit): ")
    if user_input.lower() == "exit":
        print("Goodbye!")
        break

    # Parse user input
    parsed_input = parse_user_input(user_input)
    print(f"**** parsed input  *** {parsed_input}")
    print(f"**** parsed input  *** {type(parsed_input)}")
    if not parsed_input:
        print("I'm sorry, I couldn't understand your request. Please try again.")
        continue

    try:
        # Pass the parsed input to the agent
        print({"input": parsed_input})
        print(f'{user_input} and possible input values are {parsed_input}')
        response = agent.invoke({"input": f'{user_input} and possible input values are {parsed_input}'})
        print(response["output"])
    except Exception as e:
        print(f"An error occurred: {str(e)}")