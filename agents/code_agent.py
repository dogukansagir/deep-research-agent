import config
from prompts import code_prompt
from schemas import AgentTask, CodeResult
from llm_client import llm_client

def code_agent(task: AgentTask) -> dict[str, CodeResult]:
    response = llm_client.chat.completions.create(
        model=config.DEEPSEEK_MODEL,
        response_model=CodeResult,
        messages=[{"role": "user", "content": code_prompt(task.query)}]
    )
    return {"code_result": response}