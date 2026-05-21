import config
from prompts import planner_prompt
from schemas import AgentState, ExecutionPlan
from llm_client import llm_client

def planner(state: AgentState):

    query = state["query"]
    result = llm_client.chat.completions.create(
    model=config.DEEPSEEK_MODEL,
    response_model=ExecutionPlan,
    messages=[{"role": "user", "content": planner_prompt(query)}]
    )

    return {"execution_plan": result}