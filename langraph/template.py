# Installation commands (run these in a Databricks notebook cell)
# %pip install --upgrade mlflow langgraph langchain-databricks

import mlflow
from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_databricks import ChatDatabricks
import langchain_databricks
import langgraph

# Print versions for compatibility check
print(f"langchain-databricks version: {langchain_databricks.__version__}")
print(f"langgraph version: {langgraph.__version__}")

# Enable MLflow autologging for LangGraph tracing
mlflow.langchain.autolog()

# Configure Databricks LLM endpoint (replace with your endpoint name)
llm = ChatDatabricks(
    endpoint="your-llm-endpoint-name",  # Replace with your Databricks Model Serving endpoint
    temperature=0.7,
    max_tokens=512
)

# Define the agent state
class AgentState:
    def __init__(self):
        self.messages = []

# Define the prompt template
prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="You are a helpful assistant answering user queries."),
    HumanMessage(content="{{input}}")
])

# Define the node function for the agent
def call_llm(state: AgentState):
    input_message = state.messages[-1].content
    response = llm.invoke(prompt.format(input=input_message))
    state.messages.append(response)
    return state

# Create the LangGraph workflow
workflow = StateGraph(AgentState)
workflow.add_node("llm_node", call_llm)
workflow.set_entry_point("llm_node")
workflow.set_finish_point("llm_node")

# Compile the graph
graph = workflow.compile()

# Example usage
def main():
    # Initialize state
    state = AgentState()
    state.messages.append(HumanMessage(content="What is the capital of France?"))
    
    # Run the graph
    result = graph.invoke(state)
    
    # Print the response
    print(result.messages[-1].content)

if __name__ == "__main__":
    main()
