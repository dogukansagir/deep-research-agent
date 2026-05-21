from pydantic import BaseModel, Field
from schemas import AgentState, EvalResult
from prompts import critic_prompt
import config
from llm_client import llm_client
from langfuse import observe

class ScoringResult(BaseModel):
    faithfulness_score: float = Field(le=1.0, ge=0.0, description="A score between 0 and 1 indicating the faithfulness of the synthesized answer to the original query and the provided evidence.")
    answer_relevance_score: float = Field(le=1.0, ge=0.0, description="A score between 0 and 1 indicating the relevance of the synthesized answer to the original query.")
    answer_completeness_score: float = Field(le=1.0, ge=0.0, description="A score between 0 and 1 indicating the completeness of the synthesized answer in addressing all aspects of the original query.")
    reasoning: str = Field(..., description="Detailed feedback on the agent's performance based on the evaluation criteria.")

@observe()
def critic(state: AgentState) -> ScoringResult:
    scoring = llm_client.chat.completions.create(
        model=config.DEEPSEEK_MODEL,
        response_model=ScoringResult,
        messages=[{"role": "user", "content": critic_prompt(state["query"], state["web_results"], state["academic_results"], state["code_result"], state["synthesized_answer"].answer)}]
    )
    eval_result = EvalResult(
        faithfulness_score=scoring.faithfulness_score,
        answer_relevance_score=scoring.answer_relevance_score,
        answer_completeness_score=scoring.answer_completeness_score,
        overall_score=(scoring.faithfulness_score + scoring.answer_relevance_score + scoring.answer_completeness_score) / 3,
        should_retry=(scoring.faithfulness_score < 0.7 or scoring.answer_relevance_score < 0.7 or scoring.answer_completeness_score < 0.7),
        reasoning=scoring.reasoning
    )
    return {"eval_result": eval_result, "retry_count": state["retry_count"] + 1}