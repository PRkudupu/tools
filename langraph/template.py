%pip install -U langgraph langchain_databricks langchain_core langchain
dbutils.library.restartPython()

SERVING_ENDPOINT = "dbrx-instruct"   # ← change to your Serving endpoint name

from langchain.tools import tool

@tool
def add(a: int, b: int) -> int:
    """Add two integers and return the result."""
    return a + b

@tool
def shout(text: str) -> str:
    """Uppercase a short string and add an exclamation."""
    return text.upper() + "!"
    
TOOLS = [add, shout]

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from langchain_databricks import ChatDatabricks
from langchain_core.messages import HumanMessage, AIMessage

# --- Shared state (a chat transcript) ---
class AgentState(TypedDict):
    messages: List

# --- Databricks chat model (bind tools for structured tool-calling) ---
model = ChatDatabricks(
    endpoint=SERVING_ENDPOINT,
    extra_params={"temperature": 0.2, "max_tokens": 512},
).bind_tools(TOOLS)

# --- Node: LLM step (append the model's reply to messages) ---
def llm_node(state: AgentState) -> AgentState:
    ai = model.invoke(state["messages"])
    return {"messages": state["messages"] + [ai]}

# --- Tool execution node (runs any requested tools) ---
tool_node = ToolNode(TOOLS)

# --- Router: should we call tools? ---
def needs_tools(state: AgentState) -> str:
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return "end"

# --- Wire the graph ---
g = StateGraph(AgentState)
g.add_node("llm", llm_node)
g.add_node("tools", tool_node)

g.add_edge(START, "llm")
g.add_conditional_edges("llm", needs_tools, {"tools": "tools", "end": END})
g.add_edge("tools", "llm")   # loop: tool results -> llm for final answer

memory = MemorySaver()
graph = g.compile(checkpointer=memory)

# NEW thread
config = {"configurable": {"thread_id": "demo-thread"}}

# Example A: forces a tool call (addition), then model summarizes
out = graph.invoke(
    {"messages": [HumanMessage(content="Please use your tool to add 7 and 12, then explain briefly.")]},
    config=config,
)
print(out["messages"][-1].content)

# Example B: another tool (string op)
out = graph.invoke(
    {"messages": [HumanMessage(content="Use the shout tool on 'go langgraph' and give me the result.")]},
    config=config,
)
print(out["messages"][-1].content)




