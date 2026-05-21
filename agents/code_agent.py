import instructor
from openai import OpenAI
import config
from prompts import code_prompt
from schemas import AgentTask, CodeResult

client = instructor.from_openai(
    OpenAI(api_key=config.DEEPSEEK_API_KEY, base_url=config.DEEPSEEK_API_URL)
)

def code_agent(task: AgentTask) -> CodeResult:
    response = client.chat.completions.create(
        model=config.DEEPSEEK_MODEL,
        response_model=CodeResult,
        messages=[{"role": "user", "content": code_prompt(task.query)}]
    )
    return response