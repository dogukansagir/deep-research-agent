from openai import OpenAI
import instructor
import config
from prompts import planner_prompt
from schemas import AgentState, ExecutionPlan

client = instructor.from_openai(
    OpenAI(api_key=config.DEEPSEEK_API_KEY, base_url=config.DEEPSEEK_API_URL)
)

def planner(state: AgentState):

    query = state["query"]
    result = client.chat.completions.create(
    model=config.DEEPSEEK_MODEL,
    response_model=ExecutionPlan,
    messages=[{"role": "user", "content": planner_prompt(query)}]
    )

    return {"execution_plan": result}