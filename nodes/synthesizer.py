from langchain_core.messages import HumanMessage
from schemas import AgentState, SynthesizedAnswer
import config
from prompts import synthesizer_prompt
from llm_client import llm_client
from langfuse import observe

@observe()
def synthesizer(state: AgentState) -> SynthesizedAnswer:
    response = llm_client.chat.completions.create(
        model=config.DEEPSEEK_MODEL,
        response_model=SynthesizedAnswer,
        messages=[
        {"role": "user" if isinstance(m, HumanMessage) else "assistant", "content": m.content} for m in state["conversation_history"]]+
        [{"role": "user", "content": synthesizer_prompt(state["query"], state["web_results"], state["academic_results"], state["code_result"])}]
    )
    return {"synthesized_answer": response}