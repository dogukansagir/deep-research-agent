from langgraph.graph import StateGraph, END
from schemas import AgentState
from agents.planner import planner
from agents.academic_search import academic_search_agent
from agents.web_search import web_search_agent
from agents.code_agent import code_agent
from nodes.synthesizer import synthesizer
from nodes.critic import critic
from langgraph.types import Send


def dispatch_agents(state: AgentState):
    sends = []
    for task in state["execution_plan"].tasks:
        if task.task_agent == "web_search_agent":
            sends.append(Send("web_search_agent", task))
        elif task.task_agent == "academic_search_agent":
            sends.append(Send("academic_search_agent", task))
        elif task.task_agent == "code_agent":
            sends.append(Send("coding_agent", task))
    return sends

def retry_condition(state: AgentState) -> str:
    if state["eval_result"].should_retry and state["retry_count"] < 3:
        return "synthesizer_agent"
    return "finalize"

def finalize(state: AgentState):
    return {"final_answer": state["synthesized_answer"].answer}

graph = StateGraph(AgentState)

graph.add_node("planner_agent", planner)
graph.add_node("academic_search_agent", academic_search_agent)
graph.add_node("web_search_agent", web_search_agent)
graph.add_node("coding_agent", code_agent)
graph.add_node("synthesizer_agent", synthesizer)
graph.add_node("critic_agent", critic)
graph.add_node("finalize", finalize)

graph.add_conditional_edges(
    "planner_agent",
    dispatch_agents,
)

graph.add_edge("academic_search_agent", "synthesizer_agent")
graph.add_edge("web_search_agent", "synthesizer_agent")
graph.add_edge("coding_agent", "synthesizer_agent")
graph.add_edge("synthesizer_agent", "critic_agent")

graph.add_conditional_edges(
    "critic_agent",
    retry_condition,
    {
        "synthesizer_agent": "synthesizer_agent",
        "finalize": "finalize"
    }
)

graph.add_edge("finalize", END)

graph.set_entry_point("planner_agent")

app = graph.compile()