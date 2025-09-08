%pip install -U langgraph langchain_databricks langchain_core langchain
dbutils.library.restartPython()

SERVING_ENDPOINT = "dbrx-instruct"   # ← change to your Serving endpoint name

llm = ChatDatabricks(
    endpoint=SERVING_ENDPOINT,
    extra_params={"temperature": 0.2, "max_tokens": 512},
)

def add(a: int, b: int) -> int:
    return a + b

def shout(text: str) -> str:
    return text.upper() + "!"


import json
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage

SYSTEM_PLAN = (
    "You are a routing planner. ALWAYS reply with a single JSON object ONLY, no prose.\n"
    "Schema: {\"action\": \"add|shout|none\", \"args\": {...}}\n"
    "Examples:\n"
    "- User: 'add 7 and 12' -> {\"action\":\"add\",\"args\":{\"a\":7,\"b\":12}}\n"
    "- User: 'make go langgraph loud' -> {\"action\":\"shout\",\"args\":{\"text\":\"go langgraph\"}}\n"
    "- If no tool fits -> {\"action\":\"none\",\"args\":{}}\n"
)

SYSTEM_FINALIZE = (
    "You are a helpful assistant. Given the user request and (optional) tool result, reply concisely."
)

class AgentState(TypedDict):
    messages: List      # chat transcript
    plan: Optional[dict]
    tool_result: Optional[str]

# ---- Nodes ----
def plan_node(state: AgentState) -> AgentState:
    user_msg = state["messages"][-1]
    resp = llm.invoke([{"role":"system","content":SYSTEM_PLAN}, user_msg])
    # Parse JSON safely
    try:
        plan = json.loads(resp.content if isinstance(resp, AIMessage) else resp["content"])
    except Exception:
        plan = {"action": "none", "args": {}}
    return {"plan": plan}

def tool_node(state: AgentState) -> AgentState:
    plan = state["plan"] or {"action":"none","args":{}}
    action, args = plan.get("action","none"), plan.get("args",{})
    try:
        if action == "add":
            res = str(add(int(args.get("a",0)), int(args.get("b",0))))
        elif action == "shout":
            res = shout(str(args.get("text","")))
        else:
            res = ""
    except Exception as e:
        res = f"(tool error) {e}"
    return {"tool_result": res}

def finalize_node(state: AgentState) -> AgentState:
    msgs = [{"role":"system","content":SYSTEM_FINALIZE}]
    # Include original user request and tool result (if any)
    msgs += state["messages"]
    if state.get("tool_result"):
        msgs.append({"role":"system","content":f"Tool result: {state['tool_result']}"})
    out = llm.invoke(msgs)
    return {"messages": state["messages"] + [out]}

def needs_tool(state: AgentState) -> str:
    action = (state.get("plan") or {}).get("action","none")
    return "do_tool" if action in {"add","shout"} else "skip_tool"

# ---- Wire graph ----
g = StateGraph(AgentState)
g.add_node("plan", plan_node)
g.add_node("call_tool", tool_node)
g.add_node("finalize", finalize_node)

g.add_edge(START, "plan")
g.add_conditional_edges("plan", needs_tool, {"do_tool":"call_tool", "skip_tool":"finalize"})
g.add_edge("call_tool", "finalize")

graph = g.compile(checkpointer=MemorySaver())
