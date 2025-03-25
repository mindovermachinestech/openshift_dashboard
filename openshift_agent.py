from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain.agents import Tool
from dotenv import load_dotenv
import os
from dataclasses import dataclass

# Load environment variables from .env
load_dotenv()

# Get AI Together API key from environment variable
ait_api_key = os.getenv("AIT_API_KEY")

if not ait_api_key:
    raise ValueError("AI Together API key is missing. Please set it in the .env file.")

from openshift import (
    get_applications,
    get_pods_for_application,
    restart_application,
    upgrade_application,
)

# Define tools for LangGraph agent
tools = [
    Tool(name="GetApplications", func=get_applications, description="Get a list of applications running in OpenShift."),
    Tool(name="GetPods", func=get_pods_for_application, description="Get a list of pods for a specific application."),
    Tool(name="RestartApplication", func=restart_application, description="Restart an OpenShift application."),
    Tool(name="UpgradeApplication", func=upgrade_application, description="Upgrade an application with a new image."),
]

# Initialize LLM using AI Together
llm = ChatOpenAI(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    openai_api_key=ait_api_key,
    base_url="https://api.together.xyz/v1",
)
llm.verbose = True
# Create a LangGraph ReAct agent with your tools
react_agent = create_react_agent(llm, tools)

# Define a simple state for LangGraph
@dataclass
class AgentState:
    input_text: str
    output_text: str = None

def process_request(state):
    """Process user input and get response from the agent."""
    user_input = state.input_text
    response = react_agent.invoke({"input": user_input})

    # Ensure response is passed correctly to the next state or ends
    if response:
        return AgentState(input_text=user_input, output_text=response)
    else:
        # In case of an invalid response, end gracefully
        return AgentState(input_text=user_input, output_text="No valid response.")

# Create LangGraph StateGraph
workflow = StateGraph(AgentState)

# Define flow: Start → Process Request → End
workflow.add_node("process_request", process_request)
workflow.set_entry_point("process_request")
workflow.add_edge("process_request", END)

# Compile the graph
app_graph = workflow.compile()

def process_request(user_input):
    """Handle natural language request and return response."""
    state = AgentState(input_text=user_input)

    # Correct way to invoke the graph
    result = app_graph.invoke(state, config={"recursion_limit": 50, "verbose": True})

    # Check if output_text is set correctly
    if result.output_text:
        return result.output_text
    else:
        raise ValueError("No output returned from the agent. Check the agent or workflow logic.")



